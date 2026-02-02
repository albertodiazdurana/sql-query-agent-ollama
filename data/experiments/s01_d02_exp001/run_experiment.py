"""EXP-001 Experiment Runner

Reconstructs the full SQL agent pipeline and runs evaluation for a given model.
Extracted from notebook Cells 1-29 for reproducible, script-based execution.

Usage (from project root):
    python data/experiments/s01_d02_exp001/run_experiment.py sqlcoder:7b
    python data/experiments/s01_d02_exp001/run_experiment.py llama3.1:8b

Results saved to: data/experiments/s01_d02_exp001/results_<model_slug>.json
"""

import sys
import re
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import TypedDict, Optional

from sqlalchemy import create_engine, inspect, text
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
import sqlglot

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from eval_harness import run_evaluation, save_results

# ──────────────────────────────────────────────────────────────
# Configuration (from notebook Cell 2)
# ──────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://172.27.64.1:11434"
DB_PATH = PROJECT_ROOT / "data" / "chinook.db"

# ──────────────────────────────────────────────────────────────
# Database setup (from notebook Cells 3, 7)
# ──────────────────────────────────────────────────────────────
engine = create_engine(f"sqlite:///{DB_PATH}")
inspector = inspect(engine)
tables = inspector.get_table_names()

schema_info = {}
for table_name in tables:
    columns = inspector.get_columns(table_name)
    pk = inspector.get_pk_constraint(table_name)
    fks = inspector.get_foreign_keys(table_name)
    schema_info[table_name] = {
        "columns": columns,
        "pk": pk.get("constrained_columns", []),
        "fks": fks,
    }

sample_tables = ["Artist", "Album", "Track", "Customer", "Invoice", "InvoiceLine"]
sample_rows = {}
with engine.connect() as conn:
    for table_name in sample_tables:
        rows = conn.execute(text(f"SELECT * FROM [{table_name}] LIMIT 3")).fetchall()
        keys = conn.execute(text(f"SELECT * FROM [{table_name}] LIMIT 1")).keys()
        sample_rows[table_name] = {"columns": list(keys), "rows": rows}

# ──────────────────────────────────────────────────────────────
# Column mapping for post-processing (from notebook Cells 22-23)
# ──────────────────────────────────────────────────────────────
def build_column_map():
    """Build case-insensitive column name mapping, including snake_case variants."""
    col_map = {}
    for table_name, info in schema_info.items():
        for col in info["columns"]:
            actual = col["name"]
            col_map[actual.lower()] = actual
            snake = re.sub(r'(?<!^)(?=[A-Z])', '_', actual).lower()
            col_map[snake] = actual
        col_map[table_name.lower()] = table_name
    return col_map

COLUMN_MAP = build_column_map()

def postprocess_sql(sql: str) -> str:
    """Fix known SQLite incompatibilities in generated SQL (DEC-004)."""
    original = sql
    sql = re.sub(r'\bILIKE\b', 'LIKE', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\s+NULLS\s+(FIRST|LAST)\b', '', sql, flags=re.IGNORECASE)

    sql_keywords = {
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'GROUP', 'BY', 'ORDER',
        'HAVING', 'LIMIT', 'AS', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'IS',
        'NULL', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'DESC', 'ASC',
        'DISTINCT', 'BETWEEN', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'INNER', 'LEFT', 'RIGHT', 'OUTER', 'UNION', 'ALL', 'EXISTS',
        'CAST', 'LOWER', 'UPPER', 'LENGTH', 'SUBSTR', 'TRIM',
    }

    def replace_identifier(match):
        word = match.group(0)
        if word.upper() in sql_keywords:
            return word
        lookup = word.lower().replace('"', '').replace("'", '')
        if lookup in COLUMN_MAP:
            return COLUMN_MAP[lookup]
        return word

    sql = re.sub(r'"?\b[A-Za-z_]\w*\b"?', replace_identifier, sql)

    if sql != original:
        changes = []
        if 'ILIKE' in original.upper() and 'ILIKE' not in sql.upper():
            changes.append("ILIKE->LIKE")
        if re.search(r'NULLS\s+(FIRST|LAST)', original, re.IGNORECASE):
            changes.append("removed NULLS FIRST/LAST")
        if sql.lower() != original.lower():
            changes.append("fixed column casing")
        print(f"  Post-processed: {', '.join(changes)}")

    return sql

# ──────────────────────────────────────────────────────────────
# Agent state (from notebook Cell 9)
# ──────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    question: str
    relevant_tables: list[str]
    schema_text: str
    generated_sql: str
    is_valid: bool
    validation_error: str
    results: Optional[list]
    error: str
    retry_count: int
    model_name: str

# ──────────────────────────────────────────────────────────────
# Prompt templates (from notebook Cells 13, 16)
# ──────────────────────────────────────────────────────────────
GENERIC_PROMPT = """You are a SQL expert. Generate a SQLite-compatible SELECT query for the question below.

Schema:
{schema_text}

Rules:
- Return ONLY the SQL query, no explanation
- Use only SELECT statements
- Use only tables and columns from the schema above
- Use SQLite syntax

Question: {question}

SQL:"""

SQLCODER_PROMPT = """### Task
Generate a SQL query to answer the following question:
`{question}`

### Database Schema
{schema_text}

### Answer
Given the database schema, here is the SQL query that answers `{question}`:
```sql
"""

ERROR_REPAIR_GENERIC = """The following SQL query produced an error. Fix it.

Schema:
{schema_text}

Original question: {question}

Failed SQL:
{generated_sql}

Error:
{error}

Return ONLY the corrected SQL query, no explanation.

SQL:"""

ERROR_REPAIR_SQLCODER = """### Task
The following SQL query produced an error. Fix the query to answer:
`{question}`

### Database Schema
{schema_text}

### Failed Query
{generated_sql}

### Error
{error}

### Corrected Answer
```sql
"""

# ──────────────────────────────────────────────────────────────
# Agent nodes (from notebook Cells 10, 24, 14, 15)
# ──────────────────────────────────────────────────────────────
def schema_filter(state: AgentState) -> dict:
    """Select relevant tables based on question keywords (Node 1)."""
    question_lower = state["question"].lower()
    question_words = set(question_lower.replace("?", "").replace(",", "").split())

    scored_tables = []
    for table_name, info in schema_info.items():
        score = 0
        table_lower = table_name.lower()
        if table_lower in question_lower:
            score += 3
        for word in question_words:
            if word in table_lower or table_lower in word:
                score += 2
        for col in info["columns"]:
            col_lower = col["name"].lower()
            if col_lower in question_lower:
                score += 1
            for word in question_words:
                if word in col_lower:
                    score += 0.5

        if score > 0:
            scored_tables.append((table_name, score))

    scored_tables.sort(key=lambda x: x[1], reverse=True)
    selected = [t[0] for t in scored_tables[:5]]

    for table_name in list(selected):
        for fk in schema_info[table_name]["fks"]:
            referred = fk["referred_table"]
            if referred not in selected:
                selected.append(referred)

    if not selected:
        selected = list(schema_info.keys())

    schema_lines = []
    for table_name in selected:
        info = schema_info[table_name]
        cols = ", ".join(f"{c['name']} {c['type']}" for c in info["columns"])
        schema_lines.append(f"CREATE TABLE {table_name} ({cols});")
        if table_name in sample_rows:
            sr = sample_rows[table_name]
            schema_lines.append(f"-- Sample: {sr['rows'][0]}")

    schema_text = "\n".join(schema_lines)
    print(f"  Tables: {selected}")

    return {"relevant_tables": selected, "schema_text": schema_text}


def generate_sql(state: AgentState) -> dict:
    """Generate SQL from question + filtered schema using LLM (Node 2, with post-processing)."""
    model = state["model_name"]
    template = SQLCODER_PROMPT if "sqlcoder" in model else GENERIC_PROMPT

    prompt = template.format(
        schema_text=state["schema_text"],
        question=state["question"],
    )

    llm = ChatOllama(model=model, base_url=OLLAMA_BASE_URL, temperature=0)

    t0 = time.time()
    response = llm.invoke(prompt)
    elapsed = time.time() - t0

    sql = response.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    sql = sql.rstrip(";").strip()
    sql = postprocess_sql(sql)

    print(f"  SQL ({elapsed:.1f}s): {sql[:75]}")
    return {"generated_sql": sql}


BLOCKED_KEYWORDS = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"}

def validate_query(state: AgentState) -> dict:
    """Validate SQL with sqlglot and block write operations (Node 3)."""
    sql = state["generated_sql"]

    if not sql.strip():
        return {"is_valid": False, "validation_error": "LLM returned empty SQL"}

    sql_upper = sql.upper()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in sql_upper.split():
            return {"is_valid": False, "validation_error": f"Write operation blocked: {keyword}"}

    try:
        parsed = sqlglot.parse(sql, read="sqlite")
        if not parsed or parsed[0] is None:
            return {"is_valid": False, "validation_error": "sqlglot failed to parse SQL"}
        return {"is_valid": True, "validation_error": ""}
    except sqlglot.errors.ParseError as e:
        return {"is_valid": False, "validation_error": str(e)}


def execute_query(state: AgentState) -> dict:
    """Execute validated SQL against the database (Node 4)."""
    sql = state["generated_sql"]
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchmany(20)
            results = [list(row) for row in rows]
            return {"results": results, "error": ""}
    except Exception as e:
        return {"results": None, "error": str(e)}


def handle_error(state: AgentState) -> dict:
    """Feed error back to LLM for SQL repair, with post-processing (Node 5)."""
    model = state["model_name"]
    template = ERROR_REPAIR_SQLCODER if "sqlcoder" in model else ERROR_REPAIR_GENERIC

    prompt = template.format(
        schema_text=state["schema_text"],
        question=state["question"],
        generated_sql=state["generated_sql"],
        error=state["error"],
    )

    llm = ChatOllama(model=model, base_url=OLLAMA_BASE_URL, temperature=0)

    t0 = time.time()
    response = llm.invoke(prompt)
    elapsed = time.time() - t0

    sql = response.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    sql = sql.rstrip(";").strip()
    sql = postprocess_sql(sql)

    new_retry = state["retry_count"] + 1
    print(f"  Retry {new_retry} ({elapsed:.1f}s): {sql[:75]}")
    return {"generated_sql": sql, "retry_count": new_retry, "error": ""}


# ──────────────────────────────────────────────────────────────
# Graph construction (from notebook Cells 17, 24)
# ──────────────────────────────────────────────────────────────
def should_retry(state: AgentState) -> str:
    if state["error"] and state["retry_count"] < 3:
        return "handle_error"
    return END

def check_validation(state: AgentState) -> str:
    if state["is_valid"]:
        return "execute_query"
    if state["retry_count"] < 3:
        return "handle_error"
    return END

def build_agent() -> StateGraph:
    """Build and compile the LangGraph agent."""
    workflow = StateGraph(AgentState)
    workflow.add_node("schema_filter", schema_filter)
    workflow.add_node("generate_sql", generate_sql)
    workflow.add_node("validate_query", validate_query)
    workflow.add_node("execute_query", execute_query)
    workflow.add_node("handle_error", handle_error)
    workflow.set_entry_point("schema_filter")
    workflow.add_edge("schema_filter", "generate_sql")
    workflow.add_edge("generate_sql", "validate_query")
    workflow.add_conditional_edges("validate_query", check_validation)
    workflow.add_conditional_edges("execute_query", should_retry)
    workflow.add_edge("handle_error", "validate_query")
    return workflow.compile()


# ──────────────────────────────────────────────────────────────
# Test suite (from notebook Cell 27)
# ──────────────────────────────────────────────────────────────
@dataclass
class TestQuery:
    id: str
    difficulty: str
    question: str
    expected_description: str
    expected_tables: list[str] = field(default_factory=list)

TEST_SUITE = [
    # Easy (5)
    TestQuery("E1", "Easy", "How many employees are there?",
             "Single number: 8", ["Employee"]),
    TestQuery("E2", "Easy", "List all media types",
             "5 types returned", ["MediaType"]),
    TestQuery("E3", "Easy", "What is the most expensive track?",
             "Track with max UnitPrice", ["Track"]),
    TestQuery("E4", "Easy", "How many customers are from Brazil?",
             "Single count of Brazilian customers", ["Customer"]),
    TestQuery("E5", "Easy", "Show the 5 longest tracks by duration",
             "5 tracks ordered by Milliseconds DESC", ["Track"]),
    # Medium (5)
    TestQuery("M1", "Medium", "Which genre has the most tracks?",
             "Rock with 1,297 tracks", ["Track", "Genre"]),
    TestQuery("M2", "Medium", "How much has each customer spent in total? Show top 5.",
             "Top 5 customers by SUM(Invoice.Total)", ["Customer", "Invoice"]),
    TestQuery("M3", "Medium", "List albums that have more than 20 tracks",
             "Albums with track count > 20", ["Album", "Track"]),
    TestQuery("M4", "Medium", "Which employees support the most customers?",
             "Employees ranked by customer count", ["Employee", "Customer"]),
    TestQuery("M5", "Medium", "What are the top 3 best-selling genres by revenue?",
             "Genres by SUM(UnitPrice * Quantity) from InvoiceLine",
             ["Genre", "Track", "InvoiceLine"]),
    # Hard (4)
    TestQuery("H1", "Hard", "Which artists have tracks in more than 2 genres?",
             "Artists with genre count > 2",
             ["Artist", "Album", "Track", "Genre"]),
    TestQuery("H2", "Hard",
             "Find customers who have never purchased a Jazz track",
             "Customers NOT IN Jazz purchases",
             ["Customer", "Invoice", "InvoiceLine", "Track", "Genre"]),
    TestQuery("H3", "Hard",
             "What is the average invoice total by country, only for countries with more than 5 customers?",
             "Countries with >5 customers showing AVG(Total)",
             ["Customer", "Invoice"]),
    TestQuery("H4", "Hard",
             "List the top 3 playlists by total track duration in hours",
             "Playlists by SUM(Milliseconds)/3600000",
             ["Playlist", "PlaylistTrack", "Track"]),
]


def compute_ground_truth() -> dict:
    """Compute ground truth by running known-correct SQL."""
    gt = {}
    with engine.connect() as conn:
        gt["E1"] = conn.execute(text("SELECT COUNT(*) FROM Employee")).scalar()
        gt["E2"] = conn.execute(text("SELECT COUNT(*) FROM MediaType")).scalar()
        gt["E3"] = conn.execute(text(
            "SELECT Name, UnitPrice FROM Track ORDER BY UnitPrice DESC LIMIT 1"
        )).fetchone()
        gt["E4"] = conn.execute(text(
            "SELECT COUNT(*) FROM Customer WHERE Country = 'Brazil'"
        )).scalar()
        gt["E5"] = conn.execute(text(
            "SELECT Name, Milliseconds FROM Track ORDER BY Milliseconds DESC LIMIT 5"
        )).fetchall()
        gt["M1"] = conn.execute(text(
            "SELECT g.Name, COUNT(t.TrackId) as cnt FROM Genre g "
            "JOIN Track t ON g.GenreId = t.GenreId "
            "GROUP BY g.Name ORDER BY cnt DESC LIMIT 1"
        )).fetchone()
        gt["M2"] = conn.execute(text(
            "SELECT c.FirstName, c.LastName, SUM(i.Total) as total "
            "FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId "
            "GROUP BY c.CustomerId ORDER BY total DESC LIMIT 5"
        )).fetchall()
        gt["M3"] = conn.execute(text(
            "SELECT a.Title, COUNT(t.TrackId) as cnt FROM Album a "
            "JOIN Track t ON a.AlbumId = t.AlbumId "
            "GROUP BY a.AlbumId HAVING cnt > 20 ORDER BY cnt DESC"
        )).fetchall()
        gt["M4"] = conn.execute(text(
            "SELECT e.FirstName, e.LastName, COUNT(c.CustomerId) as cnt "
            "FROM Employee e JOIN Customer c ON e.EmployeeId = c.SupportRepId "
            "GROUP BY e.EmployeeId ORDER BY cnt DESC"
        )).fetchall()
        gt["M5"] = conn.execute(text(
            "SELECT g.Name, SUM(il.UnitPrice * il.Quantity) as revenue "
            "FROM Genre g JOIN Track t ON g.GenreId = t.GenreId "
            "JOIN InvoiceLine il ON t.TrackId = il.TrackId "
            "GROUP BY g.Name ORDER BY revenue DESC LIMIT 3"
        )).fetchall()
        gt["H1"] = conn.execute(text(
            "SELECT ar.Name, COUNT(DISTINCT g.GenreId) as genre_count "
            "FROM Artist ar JOIN Album al ON ar.ArtistId = al.ArtistId "
            "JOIN Track t ON al.AlbumId = t.AlbumId "
            "JOIN Genre g ON t.GenreId = g.GenreId "
            "GROUP BY ar.ArtistId HAVING genre_count > 2 ORDER BY genre_count DESC"
        )).fetchall()
        gt["H2"] = conn.execute(text(
            "SELECT COUNT(*) FROM Customer WHERE CustomerId NOT IN ("
            "SELECT DISTINCT c.CustomerId FROM Customer c "
            "JOIN Invoice i ON c.CustomerId = i.CustomerId "
            "JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId "
            "JOIN Track t ON il.TrackId = t.TrackId "
            "JOIN Genre g ON t.GenreId = g.GenreId "
            "WHERE g.Name = 'Jazz')"
        )).scalar()
        gt["H3"] = conn.execute(text(
            "SELECT c.Country, AVG(i.Total) as avg_total, COUNT(DISTINCT c.CustomerId) as cust_count "
            "FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId "
            "GROUP BY c.Country HAVING cust_count > 5 ORDER BY avg_total DESC"
        )).fetchall()
        gt["H4"] = conn.execute(text(
            "SELECT p.Name, SUM(t.Milliseconds) / 3600000.0 as hours "
            "FROM Playlist p JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId "
            "JOIN Track t ON pt.TrackId = t.TrackId "
            "GROUP BY p.PlaylistId ORDER BY hours DESC LIMIT 3"
        )).fetchall()

    # Convert SQLAlchemy Row objects to plain tuples for serialization
    for key in gt:
        val = gt[key]
        if hasattr(val, '_mapping'):
            gt[key] = tuple(val)
        elif isinstance(val, list):
            gt[key] = [tuple(row) if hasattr(row, '_mapping') else row for row in val]

    return gt


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_experiment.py <model_name>")
        print("  e.g.: python scripts/run_experiment.py sqlcoder:7b")
        print("        python scripts/run_experiment.py llama3.1:8b")
        sys.exit(1)

    model_name = sys.argv[1]
    model_slug = model_name.replace(":", "_").replace(".", "_")

    print(f"Building agent...")
    graph = build_agent()
    print(f"Agent compiled: {list(graph.nodes.keys())}")

    print(f"Computing ground truth...")
    ground_truth = compute_ground_truth()
    print(f"Ground truth computed for {len(ground_truth)} queries")

    results = run_evaluation(model_name, TEST_SUITE, ground_truth, graph)

    output_path = PROJECT_ROOT / "data" / "experiments" / "s01_d02_exp001" / f"results_{model_slug}.json"
    save_results(results, output_path)


if __name__ == "__main__":
    main()
