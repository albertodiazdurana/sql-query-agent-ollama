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

# Prompt types for ablation study (EXP-002)
PROMPT_ZERO_SHOT = "zero_shot"
PROMPT_FEW_SHOT = "few_shot"
PROMPT_COT = "cot"

# Schema context types for ablation study (EXP-002)
SCHEMA_FULL = "full"          # All tables in database
SCHEMA_SELECTIVE = "selective"  # Only question-relevant tables

# Generic prompt for general-purpose models (llama3.1:8b, etc.)
# Also serves as the ZERO-SHOT baseline for ablation study
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

# ──────────────────────────────────────────────────────────────
# Ablation study prompt variants (EXP-002)
# ──────────────────────────────────────────────────────────────

# Few-shot prompt with 2 examples from Chinook database
FEW_SHOT_PROMPT = """You are a SQL expert. Generate a SQLite-compatible SELECT query for the question below.

Schema:
{schema_text}

Here are some examples:

Example 1:
Question: How many employees are there?
SQL: SELECT COUNT(*) FROM Employee;

Example 2:
Question: What are the names of all albums by the artist 'AC/DC'?
SQL: SELECT Album.Title FROM Album JOIN Artist ON Album.ArtistId = Artist.ArtistId WHERE Artist.Name = 'AC/DC';

Rules:
- Return ONLY the SQL query, no explanation
- Use only SELECT statements
- Use only tables and columns from the schema above
- Use SQLite syntax

Question: {question}

SQL:"""

# Chain-of-thought prompt that reasons before generating SQL
COT_PROMPT = """You are a SQL expert. Generate a SQLite-compatible SELECT query for the question below.

Schema:
{schema_text}

Rules:
- First, identify which tables are needed
- Then, identify which columns to select
- Consider any joins, filters, or aggregations needed
- Finally, write the SQL query
- Return ONLY the SQL query at the end, no explanation

Question: {question}

Reasoning:
1. Tables needed:
2. Columns to select:
3. Joins/filters/aggregations:

SQL:"""

# ──────────────────────────────────────────────────────────────
# Error repair prompts (used by handle_error node)
# ──────────────────────────────────────────────────────────────

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


def get_ablation_prompt(prompt_type: str, model_name: str = "") -> str:
    """Return the prompt template for ablation experiments (EXP-002).

    Args:
        prompt_type: One of PROMPT_ZERO_SHOT, PROMPT_FEW_SHOT, PROMPT_COT
        model_name: Model name for model-specific prompts (e.g., sqlcoder)

    Returns:
        The prompt template string
    """
    # For sqlcoder, always use its specific format
    if "sqlcoder" in model_name:
        return SQLCODER_PROMPT

    # Ablation prompt selection for generic models
    if prompt_type == PROMPT_FEW_SHOT:
        return FEW_SHOT_PROMPT
    elif prompt_type == PROMPT_COT:
        return COT_PROMPT
    else:  # PROMPT_ZERO_SHOT or default
        return GENERIC_PROMPT
