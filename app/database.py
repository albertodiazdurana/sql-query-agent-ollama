"""Database layer for the SQL Query Agent.

Handles engine creation, schema introspection, sample row fetching,
column mapping, and SQL post-processing (DEC-004). Extracted from
notebook cells 1-7 and run_experiment.py lines 39-116.
"""

import re

from sqlalchemy import create_engine, inspect, text, Engine

from app.config import SQL_KEYWORDS


def create_db_engine(db_path: str) -> Engine:
    """Create a SQLAlchemy engine for a SQLite database."""
    return create_engine(f"sqlite:///{db_path}")


def get_schema_info(engine: Engine) -> dict:
    """Introspect all tables, columns, primary keys, and foreign keys.

    Returns:
        dict mapping table_name -> {columns, pk, fks}
    """
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

    return schema_info


def get_sample_rows(engine: Engine, tables: list[str], n: int = 3) -> dict:
    """Fetch sample rows for specified tables (used in schema context for prompts).

    Returns:
        dict mapping table_name -> {columns: [...], rows: [...]}
    """
    sample_rows = {}
    with engine.connect() as conn:
        for table_name in tables:
            rows = conn.execute(text(f"SELECT * FROM [{table_name}] LIMIT {n}")).fetchall()
            keys = conn.execute(text(f"SELECT * FROM [{table_name}] LIMIT 1")).keys()
            sample_rows[table_name] = {"columns": list(keys), "rows": rows}
    return sample_rows


def build_schema_text(schema_info: dict, tables: list[str] | None = None) -> str:
    """Build CREATE TABLE statements for schema context in prompts.

    Args:
        schema_info: Full schema from get_schema_info()
        tables: List of table names to include. If None, includes all tables.

    Returns:
        String with CREATE TABLE statements for the specified tables.
    """
    if tables is None:
        tables = list(schema_info.keys())

    lines = []
    for table_name in tables:
        if table_name not in schema_info:
            continue
        info = schema_info[table_name]
        cols = []
        for col in info["columns"]:
            col_type = str(col.get("type", "TEXT"))
            nullable = "" if col.get("nullable", True) else " NOT NULL"
            pk = " PRIMARY KEY" if col["name"] in info["pk"] else ""
            cols.append(f"  {col['name']} {col_type}{nullable}{pk}")
        lines.append(f"CREATE TABLE {table_name} (\n" + ",\n".join(cols) + "\n);")

    return "\n\n".join(lines)


def build_column_map(schema_info: dict) -> dict:
    """Build case-insensitive column name mapping, including snake_case variants.

    Maps lowercase and snake_case versions of column/table names to their
    actual PascalCase names in the database. Used by postprocess_sql to fix
    column casing in generated SQL.
    """
    col_map = {}
    for table_name, info in schema_info.items():
        for col in info["columns"]:
            actual = col["name"]
            col_map[actual.lower()] = actual
            # PascalCase -> snake_case mapping (e.g., CustomerId -> customer_id)
            snake = re.sub(r"(?<!^)(?=[A-Z])", "_", actual).lower()
            col_map[snake] = actual
        col_map[table_name.lower()] = table_name
    return col_map


def postprocess_sql(sql: str, column_map: dict) -> str:
    """Fix known SQLite incompatibilities in generated SQL (DEC-004).

    Applies three fixes:
    1. ILIKE -> LIKE (SQLite has no ILIKE)
    2. Remove NULLS FIRST/LAST (SQLite doesn't support it)
    3. Fix column/table casing (snake_case -> PascalCase)

    Returns:
        The post-processed SQL string.
    """
    # 1. ILIKE -> LIKE
    sql = re.sub(r"\bILIKE\b", "LIKE", sql, flags=re.IGNORECASE)

    # 2. Remove NULLS FIRST/LAST
    sql = re.sub(r"\s+NULLS\s+(FIRST|LAST)\b", "", sql, flags=re.IGNORECASE)

    # 3. Fix identifier casing using column_map
    def replace_identifier(match):
        word = match.group(0)
        if word.upper() in SQL_KEYWORDS:
            return word
        lookup = word.lower().replace('"', "").replace("'", "")
        if lookup in column_map:
            return column_map[lookup]
        return word

    sql = re.sub(r'"?\b[A-Za-z_]\w*\b"?', replace_identifier, sql)

    return sql
