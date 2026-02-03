"""Streamlit web interface for the SQL Query Agent.

Usage:
    streamlit run app/main.py

Features:
- Natural language to SQL conversion
- Query execution against SQLite databases
- Schema explorer with table relationships
- Error handling with retry display
- Ollama connectivity check
"""

import requests
import streamlit as st
import pandas as pd

from app.config import (
    DEFAULT_DB_PATH,
    DEFAULT_MODEL,
    OLLAMA_BASE_URL,
)
from app.database import create_db_engine, get_schema_info
from app.agent import build_agent, AgentState


# ──────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SQL Query Agent",
    page_icon="🔍",
    layout="wide",
)


# ──────────────────────────────────────────────────────────────
# Table descriptions for Chinook database
# ──────────────────────────────────────────────────────────────
TABLE_DESCRIPTIONS = {
    "Album": "Music albums with title and artist reference",
    "Artist": "Music artists/bands with their names",
    "Customer": "Store customers with contact info and support rep",
    "Employee": "Store employees with job titles and hierarchy",
    "Genre": "Music genres (Rock, Jazz, Metal, etc.)",
    "Invoice": "Customer purchase invoices with totals",
    "InvoiceLine": "Individual items on each invoice (tracks purchased)",
    "MediaType": "Audio formats (MPEG, AAC, Protected AAC, etc.)",
    "Playlist": "Named playlists (Music, Movies, etc.)",
    "PlaylistTrack": "Junction table linking playlists to tracks",
    "Track": "Individual songs with album, genre, media type, price, duration",
}


# ──────────────────────────────────────────────────────────────
# Ollama connectivity check
# ──────────────────────────────────────────────────────────────
def check_ollama() -> tuple[bool, str]:
    """Check if Ollama is running and the model is available."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            if DEFAULT_MODEL in models or any(DEFAULT_MODEL in m for m in models):
                return True, f"Connected. Model: {DEFAULT_MODEL}"
            return False, f"Model {DEFAULT_MODEL} not found. Available: {models}"
        return False, f"Ollama returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to Ollama at {OLLAMA_BASE_URL}"
    except Exception as e:
        return False, f"Error: {e}"


# ──────────────────────────────────────────────────────────────
# Agent and schema initialization (cached)
# ──────────────────────────────────────────────────────────────
@st.cache_resource
def get_agent(db_path: str, model_name: str):
    """Build and cache the agent for the given database and model."""
    engine = create_db_engine(db_path)
    return build_agent(engine, model_name), engine


@st.cache_data
def get_cached_schema(db_path: str) -> dict:
    """Get and cache schema info for display."""
    engine = create_db_engine(db_path)
    return get_schema_info(engine)


# ──────────────────────────────────────────────────────────────
# Schema explorer component
# ──────────────────────────────────────────────────────────────
def render_schema_explorer(schema_info: dict):
    """Render the schema explorer with relationships and table details."""

    # Relationship diagram (text-based)
    st.markdown("**Table Relationships**")
    st.code("""
┌─────────┐     ┌───────┐     ┌───────┐
│ Artist  │────▶│ Album │────▶│ Track │
└─────────┘     └───────┘     └───┬───┘
                                  │
        ┌─────────────────────────┼─────────────────┐
        │                         │                 │
        ▼                         ▼                 ▼
┌───────────────┐         ┌───────────┐     ┌───────────┐
│ InvoiceLine   │         │   Genre   │     │ MediaType │
└───────┬───────┘         └───────────┘     └───────────┘
        │
        ▼
┌───────────────┐     ┌──────────────┐
│   Invoice     │────▶│   Customer   │
└───────────────┘     └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │   Employee   │
                      └──────────────┘

┌───────────────┐     ┌───────────────┐
│   Playlist    │────▶│ PlaylistTrack │────▶ Track
└───────────────┘     └───────────────┘
""", language=None)

    # Table details
    st.markdown("**Table Details**")
    for table_name in sorted(schema_info.keys()):
        info = schema_info[table_name]
        desc = TABLE_DESCRIPTIONS.get(table_name, "")

        with st.expander(f"📋 {table_name}"):
            if desc:
                st.caption(desc)

            # Columns
            cols_data = []
            for col in info["columns"]:
                pk_marker = "🔑" if col["name"] in info["pk"] else ""
                cols_data.append({
                    "Column": f"{pk_marker} {col['name']}".strip(),
                    "Type": str(col["type"]),
                })
            st.dataframe(
                pd.DataFrame(cols_data),
                use_container_width=True,
                hide_index=True,
            )

            # Foreign keys
            if info["fks"]:
                fk_text = ", ".join(
                    f"{', '.join(fk['constrained_columns'])} → {fk['referred_table']}"
                    for fk in info["fks"]
                )
                st.caption(f"Foreign keys: {fk_text}")


# ──────────────────────────────────────────────────────────────
# Main app
# ──────────────────────────────────────────────────────────────
def main():
    st.title("SQL Query Agent")
    st.caption("Ask questions in natural language, get SQL and results")

    # Get schema for display
    schema_info = get_cached_schema(str(DEFAULT_DB_PATH))

    # Sidebar
    with st.sidebar:
        # Ollama status
        st.header("Status")
        ollama_ok, ollama_msg = check_ollama()
        if ollama_ok:
            st.success(ollama_msg)
        else:
            st.error(ollama_msg)
            st.stop()

        st.divider()

        # Schema explorer
        st.header("Schema Explorer")
        render_schema_explorer(schema_info)

        st.divider()

        # Query history
        st.header("History")
        if "history" not in st.session_state:
            st.session_state.history = []

        if st.session_state.history:
            for item in reversed(st.session_state.history[-5:]):
                with st.expander(f"Q: {item['question'][:25]}..."):
                    st.code(item["sql"], language="sql")
        else:
            st.caption("No queries yet")

    # Main area: question input
    question = st.text_input(
        "Ask a question about the database:",
        placeholder="e.g., How many employees are there?",
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        run_clicked = st.button("Run Query", type="primary", disabled=not question)

    # Run query
    if run_clicked and question:
        with st.spinner("Generating SQL..."):
            # Initialize agent
            agent, engine = get_agent(str(DEFAULT_DB_PATH), DEFAULT_MODEL)

            # Prepare initial state
            initial_state: AgentState = {
                "question": question,
                "relevant_tables": [],
                "schema_text": "",
                "raw_sql": "",
                "generated_sql": "",
                "is_valid": False,
                "validation_error": "",
                "results": None,
                "error": "",
                "retry_count": 0,
                "model_name": DEFAULT_MODEL,
            }

            # Run agent
            try:
                result = agent.invoke(initial_state)

                # Display SQL
                st.subheader("Generated SQL")
                st.code(result["generated_sql"], language="sql")

                # Display retry info if any
                if result["retry_count"] > 0:
                    st.warning(f"Query required {result['retry_count']} retry(s)")

                # Display results or error
                if result["error"]:
                    st.error(f"Execution error: {result['error']}")
                elif result["results"] is not None:
                    st.subheader("Results")
                    if result["results"]:
                        df = pd.DataFrame(result["results"])
                        st.dataframe(df, use_container_width=True)
                        st.caption(f"{len(result['results'])} row(s) returned")
                    else:
                        st.info("Query returned no results")

                    # Add to history
                    st.session_state.history.append({
                        "question": question,
                        "sql": result["generated_sql"],
                    })
                elif result["validation_error"]:
                    st.error(f"Validation failed: {result['validation_error']}")

            except Exception as e:
                st.error(f"Agent error: {e}")

    # Example questions
    with st.expander("Example questions"):
        st.markdown("""
        **Easy:**
        - How many employees are there?
        - List all media types
        - What is the most expensive track?

        **Medium:**
        - Which genre has the most tracks?
        - How much has each customer spent in total? Show top 5.

        **Hard:**
        - Which artists have tracks in more than 2 genres?
        - Find customers who have never purchased a Jazz track
        """)


if __name__ == "__main__":
    main()
