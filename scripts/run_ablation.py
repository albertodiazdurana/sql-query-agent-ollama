"""EXP-002 Ablation Study Runner

Systematic ablation study to measure the impact of prompt engineering choices.
Tests prompt variants (zero-shot, few-shot, CoT) and schema context (full, selective).

Usage (from project root):
    python scripts/run_ablation.py

Results saved to: data/experiments/s02_ablation/
"""

import sys
import time
import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from app.config import (
    DEFAULT_DB_PATH,
    DEFAULT_MODEL,
    OLLAMA_BASE_URL,
    PROMPT_ZERO_SHOT,
    PROMPT_FEW_SHOT,
    PROMPT_COT,
    SCHEMA_FULL,
    SCHEMA_SELECTIVE,
    get_ablation_prompt,
)
from app.database import (
    create_db_engine,
    get_schema_info,
    get_sample_rows,
    build_schema_text,
    build_column_map,
    postprocess_sql,
)
from scripts.eval_harness import compare_results, check_sql_parsable

from langchain_ollama import ChatOllama

# ──────────────────────────────────────────────────────────────
# Test Suite (from EXP-001)
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


# ──────────────────────────────────────────────────────────────
# Ground Truth
# ──────────────────────────────────────────────────────────────
def compute_ground_truth(engine) -> dict:
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

    # Convert SQLAlchemy Row objects to plain tuples
    for key in gt:
        val = gt[key]
        if hasattr(val, '_mapping'):
            gt[key] = tuple(val)
        elif isinstance(val, list):
            gt[key] = [tuple(row) if hasattr(row, '_mapping') else row for row in val]

    return gt


# ──────────────────────────────────────────────────────────────
# Schema Selection
# ──────────────────────────────────────────────────────────────
def select_tables(question: str, schema_info: dict) -> list[str]:
    """Select relevant tables based on question keywords."""
    question_lower = question.lower()
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

    # Add FK-related tables
    for table_name in list(selected):
        for fk in schema_info[table_name]["fks"]:
            referred = fk["referred_table"]
            if referred not in selected:
                selected.append(referred)

    if not selected:
        selected = list(schema_info.keys())

    return selected


# ──────────────────────────────────────────────────────────────
# Single Query Runner
# ──────────────────────────────────────────────────────────────
def run_single_query(
    question: str,
    schema_text: str,
    prompt_type: str,
    model_name: str,
    llm: ChatOllama,
    column_map: dict,
    engine,
) -> dict:
    """Run a single query and return results."""
    prompt_template = get_ablation_prompt(prompt_type, model_name)
    prompt = prompt_template.format(schema_text=schema_text, question=question)

    t0 = time.time()
    try:
        response = llm.invoke(prompt)
        latency = time.time() - t0

        raw_sql = response.content.strip()
        raw_sql = raw_sql.replace("```sql", "").replace("```", "").strip()
        raw_sql = raw_sql.rstrip(";").strip()

        # Post-process
        final_sql = postprocess_sql(raw_sql, column_map)

        # Execute
        results = None
        error = None
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(final_sql)).fetchmany(20)
                results = [list(row) for row in rows]
        except Exception as e:
            error = str(e)

        return {
            "raw_sql": raw_sql,
            "final_sql": final_sql,
            "results": results,
            "error": error,
            "latency": latency,
            "raw_parsable": check_sql_parsable(raw_sql),
        }

    except Exception as e:
        return {
            "raw_sql": None,
            "final_sql": None,
            "results": None,
            "error": str(e),
            "latency": time.time() - t0,
            "raw_parsable": False,
        }


# ──────────────────────────────────────────────────────────────
# Ablation Configuration
# ──────────────────────────────────────────────────────────────
ABLATION_CONFIGS = [
    {"prompt_type": PROMPT_ZERO_SHOT, "schema_type": SCHEMA_FULL},
    {"prompt_type": PROMPT_ZERO_SHOT, "schema_type": SCHEMA_SELECTIVE},
    {"prompt_type": PROMPT_FEW_SHOT, "schema_type": SCHEMA_FULL},
    {"prompt_type": PROMPT_FEW_SHOT, "schema_type": SCHEMA_SELECTIVE},
    {"prompt_type": PROMPT_COT, "schema_type": SCHEMA_FULL},
    {"prompt_type": PROMPT_COT, "schema_type": SCHEMA_SELECTIVE},
]


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  EXP-002: Ablation Study")
    print(f"  Model: {DEFAULT_MODEL}")
    print(f"  Configurations: {len(ABLATION_CONFIGS)}")
    print(f"  Questions: {len(TEST_SUITE)}")
    print(f"  Total runs: {len(ABLATION_CONFIGS) * len(TEST_SUITE)}")
    print("=" * 70)

    # Setup
    engine = create_db_engine(str(DEFAULT_DB_PATH))
    schema_info = get_schema_info(engine)
    column_map = build_column_map(schema_info)
    ground_truth = compute_ground_truth(engine)

    llm = ChatOllama(
        model=DEFAULT_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
    )

    # Full schema text (for SCHEMA_FULL)
    full_schema_text = build_schema_text(schema_info)

    # Results storage
    all_results = {}

    for config in ABLATION_CONFIGS:
        config_name = f"{config['prompt_type']}_{config['schema_type']}"
        print(f"\n{'─' * 70}")
        print(f"  Configuration: {config_name}")
        print(f"{'─' * 70}")

        config_results = []

        for i, tq in enumerate(TEST_SUITE):
            print(f"  [{tq.id}] {tq.question[:50]}...", end=" ", flush=True)

            # Select schema
            if config["schema_type"] == SCHEMA_SELECTIVE:
                selected_tables = select_tables(tq.question, schema_info)
                schema_text = build_schema_text(schema_info, selected_tables)
            else:
                schema_text = full_schema_text

            # Run query
            result = run_single_query(
                question=tq.question,
                schema_text=schema_text,
                prompt_type=config["prompt_type"],
                model_name=DEFAULT_MODEL,
                llm=llm,
                column_map=column_map,
                engine=engine,
            )

            # Check accuracy
            execution_accurate = compare_results(
                result["results"], ground_truth.get(tq.id), tq.id
            )

            result["query_id"] = tq.id
            result["difficulty"] = tq.difficulty
            result["execution_accurate"] = execution_accurate
            config_results.append(result)

            tag = "PASS" if execution_accurate else "FAIL"
            print(f"{tag} ({result['latency']:.1f}s)")

        all_results[config_name] = config_results

    # Summary table
    print("\n" + "=" * 70)
    print("  ABLATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'Configuration':<30} {'EX':>5} {'VV':>5} {'Latency':>8}")
    print("-" * 50)

    summary_data = []
    for config_name, results in all_results.items():
        ex = sum(r["execution_accurate"] for r in results)
        vv = sum(r["raw_parsable"] for r in results)
        avg_lat = sum(r["latency"] for r in results) / len(results)
        print(f"{config_name:<30} {ex:>2}/14 {vv:>2}/14 {avg_lat:>7.1f}s")
        summary_data.append({
            "config": config_name,
            "execution_accuracy": ex,
            "syntax_validity": vv,
            "avg_latency": round(avg_lat, 2),
        })

    # Best configuration
    best = max(summary_data, key=lambda x: x["execution_accuracy"])
    print("-" * 50)
    print(f"Best: {best['config']} (EX={best['execution_accuracy']}/14)")

    # Save results
    output_dir = PROJECT_ROOT / "data" / "experiments" / "s02_ablation"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"ablation_results_{timestamp}.json"

    output_data = {
        "experiment": "EXP-002",
        "model": DEFAULT_MODEL,
        "timestamp": timestamp,
        "summary": summary_data,
        "best_config": best["config"],
        "detailed_results": {
            config_name: [
                {
                    "query_id": r["query_id"],
                    "difficulty": r["difficulty"],
                    "execution_accurate": r["execution_accurate"],
                    "raw_parsable": r["raw_parsable"],
                    "latency": round(r["latency"], 2),
                    "final_sql": r["final_sql"],
                    "error": r["error"],
                }
                for r in results
            ]
            for config_name, results in all_results.items()
        },
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
