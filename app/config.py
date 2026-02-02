"""Configuration, prompt templates, and constants for the SQL Query Agent.

Centralizes all settings previously scattered across notebook cells and
run_experiment.py. Single source of truth for the Streamlit app, agent,
and evaluation scripts.
"""

from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "chinook.db"

# ──────────────────────────────────────────────────────────────
# Ollama connection
# ──────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://172.27.64.1:11434"

# ──────────────────────────────────────────────────────────────
# Model defaults (DEC-005: llama3.1:8b recommended)
# ──────────────────────────────────────────────────────────────
DEFAULT_MODEL = "llama3.1:8b"
TEMPERATURE = 0
NUM_CTX = 8192
MAX_RETRIES = 3

# ──────────────────────────────────────────────────────────────
# Security: blocked SQL keywords
# ──────────────────────────────────────────────────────────────
BLOCKED_KEYWORDS = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"}

# ──────────────────────────────────────────────────────────────
# SQL keywords (for post-processing identifier replacement)
# ──────────────────────────────────────────────────────────────
SQL_KEYWORDS = {
    "SELECT", "FROM", "WHERE", "JOIN", "ON", "GROUP", "BY", "ORDER",
    "HAVING", "LIMIT", "AS", "AND", "OR", "NOT", "IN", "LIKE", "IS",
    "NULL", "COUNT", "SUM", "AVG", "MIN", "MAX", "DESC", "ASC",
    "DISTINCT", "BETWEEN", "CASE", "WHEN", "THEN", "ELSE", "END",
    "INNER", "LEFT", "RIGHT", "OUTER", "UNION", "ALL", "EXISTS",
    "CAST", "LOWER", "UPPER", "LENGTH", "SUBSTR", "TRIM",
}

# ──────────────────────────────────────────────────────────────
# Prompt templates (DEC-003: model-aware prompting)
# ──────────────────────────────────────────────────────────────

# Generic prompt for general-purpose models (llama3.1:8b, etc.)
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

# sqlcoder-specific prompt format (DEC-003: requires ### Task structure)
SQLCODER_PROMPT = """### Task
Generate a SQL query to answer the following question:
`{question}`

### Database Schema
{schema_text}

### Answer
Given the database schema, here is the SQL query that answers `{question}`:
```sql
"""

# Error repair prompts (used by handle_error node)
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


def get_prompt_template(model_name: str) -> str:
    """Return the appropriate prompt template for a model (DEC-003)."""
    if "sqlcoder" in model_name:
        return SQLCODER_PROMPT
    return GENERIC_PROMPT


def get_error_repair_template(model_name: str) -> str:
    """Return the appropriate error repair template for a model (DEC-003)."""
    if "sqlcoder" in model_name:
        return ERROR_REPAIR_SQLCODER
    return ERROR_REPAIR_GENERIC
