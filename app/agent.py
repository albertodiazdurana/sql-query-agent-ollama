"""LangGraph SQL agent with schema filtering, generation, post-processing,
validation, execution, and error handling.

Extracted from run_experiment.py lines 121-369. Key changes from Sprint 1:
- Post-processing is a separate graph node (LIM-003 fix)
- raw_sql field added to AgentState for metrics
- build_agent() takes engine and model_name parameters (testable)
- Node functions use closures for dependency injection
"""

import time
from typing import TypedDict, Optional

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from sqlalchemy import Engine, text
import sqlglot

from app.config import (
    OLLAMA_BASE_URL,
    TEMPERATURE,
    NUM_CTX,
    MAX_RETRIES,
    BLOCKED_KEYWORDS,
    get_prompt_template,
    get_error_repair_template,
)
from app.database import (
    get_schema_info,
    get_sample_rows,
    build_column_map,
    postprocess_sql,
)


# ──────────────────────────────────────────────────────────────
# Agent state
# ──────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    question: str
    relevant_tables: list[str]
    schema_text: str
    raw_sql: str            # SQL before post-processing (LIM-003)
    generated_sql: str      # SQL after post-processing (used for validation/execution)
    is_valid: bool
    validation_error: str
    results: Optional[list]
    error: str
    retry_count: int
    model_name: str


# ──────────────────────────────────────────────────────────────
# Node functions
# ──────────────────────────────────────────────────────────────
def make_schema_filter(schema_info: dict, sample_rows: dict):
    """Create a schema_filter node with injected schema and sample data."""

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

        # Add FK-related tables
        for table_name in list(selected):
            for fk in schema_info[table_name]["fks"]:
                referred = fk["referred_table"]
                if referred not in selected:
                    selected.append(referred)

        if not selected:
            selected = list(schema_info.keys())

        # Build schema text with sample rows
        schema_lines = []
        for table_name in selected:
            info = schema_info[table_name]
            cols = ", ".join(f"{c['name']} {c['type']}" for c in info["columns"])
            schema_lines.append(f"CREATE TABLE {table_name} ({cols});")
            if table_name in sample_rows:
                sr = sample_rows[table_name]
                schema_lines.append(f"-- Sample: {sr['rows'][0]}")

        schema_text = "\n".join(schema_lines)
        return {"relevant_tables": selected, "schema_text": schema_text}

    return schema_filter


def make_generate_sql(model_name: str):
    """Create a generate_sql node for the given model."""

    def generate_sql(state: AgentState) -> dict:
        """Generate SQL from question + filtered schema using LLM (Node 2).

        Does NOT apply post-processing — that's now a separate node (LIM-003).
        """
        template = get_prompt_template(model_name)
        prompt = template.format(
            schema_text=state["schema_text"],
            question=state["question"],
        )

        llm = ChatOllama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=TEMPERATURE,
            num_ctx=NUM_CTX,
        )

        t0 = time.time()
        response = llm.invoke(prompt)
        elapsed = time.time() - t0

        # Extract SQL from markdown fences and strip trailing semicolons
        sql = response.content.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()
        sql = sql.rstrip(";").strip()

        print(f"  SQL ({elapsed:.1f}s): {sql[:75]}")
        return {"generated_sql": sql}

    return generate_sql


def make_postprocess_query(column_map: dict):
    """Create a postprocess_query node with injected column map (LIM-003 fix)."""

    def postprocess_query(state: AgentState) -> dict:
        """Save raw SQL, then apply dialect post-processing (Node 3 — NEW).

        This node exists so that raw_sql is captured in state before
        post-processing modifies generated_sql. Fixes LIM-003: metrics
        for raw vs post-processed SQL are now separable.
        """
        raw = state["generated_sql"]
        processed = postprocess_sql(raw, column_map)

        if processed != raw:
            print(f"  Post-processed SQL: {processed[:75]}")

        return {"raw_sql": raw, "generated_sql": processed}

    return postprocess_query


def validate_query(state: AgentState) -> dict:
    """Validate SQL with sqlglot and block write operations (Node 4)."""
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


def make_execute_query(engine: Engine):
    """Create an execute_query node with injected database engine."""

    def execute_query(state: AgentState) -> dict:
        """Execute validated SQL against the database (Node 5)."""
        sql = state["generated_sql"]
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(sql)).fetchmany(20)
                results = [list(row) for row in rows]
                return {"results": results, "error": ""}
        except Exception as e:
            return {"results": None, "error": str(e)}

    return execute_query


def make_handle_error(model_name: str, column_map: dict):
    """Create a handle_error node for the given model, with post-processing."""

    def handle_error(state: AgentState) -> dict:
        """Feed error back to LLM for SQL repair (Node 6)."""
        template = get_error_repair_template(model_name)
        prompt = template.format(
            schema_text=state["schema_text"],
            question=state["question"],
            generated_sql=state["generated_sql"],
            error=state.get("error", "") or state.get("validation_error", ""),
        )

        llm = ChatOllama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=TEMPERATURE,
            num_ctx=NUM_CTX,
        )

        t0 = time.time()
        response = llm.invoke(prompt)
        elapsed = time.time() - t0

        sql = response.content.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()
        sql = sql.rstrip(";").strip()

        # Post-process the repaired SQL too
        raw = sql
        sql = postprocess_sql(sql, column_map)

        new_retry = state["retry_count"] + 1
        print(f"  Retry {new_retry} ({elapsed:.1f}s): {sql[:75]}")
        return {"raw_sql": raw, "generated_sql": sql, "retry_count": new_retry, "error": ""}

    return handle_error


# ──────────────────────────────────────────────────────────────
# Routing functions
# ──────────────────────────────────────────────────────────────
def check_validation(state: AgentState) -> str:
    """Route after validation: execute if valid, retry or end if not."""
    if state["is_valid"]:
        return "execute_query"
    if state["retry_count"] < MAX_RETRIES:
        return "handle_error"
    return END


def should_retry(state: AgentState) -> str:
    """Route after execution: retry on error or finish."""
    if state["error"] and state["retry_count"] < MAX_RETRIES:
        return "handle_error"
    return END


# ──────────────────────────────────────────────────────────────
# Graph builder
# ──────────────────────────────────────────────────────────────
def build_agent(engine: Engine, model_name: str):
    """Construct and compile the LangGraph agent.

    New graph structure (LIM-003 fix — postprocess_query is a separate node):

        schema_filter → generate_sql → postprocess_query → validate_query → execute_query → END
                              ^                                  |                    |
                              |                                  v                    v
                              +--------------------------- handle_error <-----------+
    """
    schema_info = get_schema_info(engine)
    sample_tables = [t for t in schema_info.keys()
                     if t in ("Artist", "Album", "Track", "Customer", "Invoice", "InvoiceLine")]
    sample_rows = get_sample_rows(engine, sample_tables)
    column_map = build_column_map(schema_info)

    workflow = StateGraph(AgentState)

    workflow.add_node("schema_filter", make_schema_filter(schema_info, sample_rows))
    workflow.add_node("generate_sql", make_generate_sql(model_name))
    workflow.add_node("postprocess_query", make_postprocess_query(column_map))
    workflow.add_node("validate_query", validate_query)
    workflow.add_node("execute_query", make_execute_query(engine))
    workflow.add_node("handle_error", make_handle_error(model_name, column_map))

    workflow.set_entry_point("schema_filter")
    workflow.add_edge("schema_filter", "generate_sql")
    workflow.add_edge("generate_sql", "postprocess_query")
    workflow.add_edge("postprocess_query", "validate_query")
    workflow.add_conditional_edges("validate_query", check_validation)
    workflow.add_conditional_edges("execute_query", should_retry)
    workflow.add_edge("handle_error", "validate_query")

    return workflow.compile()
