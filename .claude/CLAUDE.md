@D:/data-science/agentic-ai-data-science-methodology/DSM_Custom_Instructions_v1.1.md

# Project: SQL Query Agent with Ollama

**Type:** Hybrid (Notebooks + Application)
**Author:** Alberto
**DSM Track:** DSM 1.0 for Sprint 1 (notebook experimentation), DSM 4.0 for Sprint 2 (Streamlit app)

---

## Project Context

- **Purpose**: Build a natural language to SQL query application powered by open-source LLMs running locally via Ollama
- **Deliverables**: Sprint 1 = Jupyter notebook prototype; Sprint 2 = Streamlit application
- **Users**: Developers and analysts who want to query SQL databases using plain English without writing SQL manually

## Technical Stack

- **LLM Runtime**: Ollama (local, no API keys)
- **Agent Framework**: LangChain + LangGraph
- **Frontend**: Streamlit (Sprint 2)
- **Database**: SQLite (primary), potential PostgreSQL/MySQL support
- **Language**: Python 3.10+
- **Key packages**: `langchain`, `langchain-community`, `langchain-ollama`, `langgraph`, `sqlalchemy`, `streamlit`, `jupyter`

## Recommended Ollama Models

| Model | Size | Notes |
|-------|------|-------|
| `llama3.1:8b` | 4.7GB | Good balance of speed and quality |
| `codellama:13b` | 7.4GB | Code-focused, better SQL syntax |
| `mistral:7b` | 4.1GB | Fast, decent SQL generation |
| `sqlcoder:7b` | 4.1GB | Specialized for SQL |

## Sprint Structure

- **Sprint 1 (Notebook Experimentation)** - DSM 1.0 track:
  - Environment setup, database setup
  - Core experimentation in Jupyter notebook
  - LangGraph agent: `generate_sql` -> `validate_query` -> `execute_query` -> `handle_error`
  - Evaluation with 10-15 sample queries
  - Deliverable: `notebooks/01_sql_agent_exploration.ipynb`

- **Sprint 2 (Streamlit Application)** - DSM 4.0 track:
  - Modular project structure (`app/main.py`, `app/agent.py`, `app/database.py`, `app/config.py`)
  - Database connection interface, NL input, SQL display, results table, query history
  - Error handling and retry logic
  - Deliverable: Functional Streamlit app

## Project Structure

```
sql-query-agent-ollama/
├── .claude/              # AI agent configuration
├── app/                  # Streamlit application (Sprint 2)
│   ├── __init__.py
│   ├── main.py           # Streamlit entry point
│   ├── agent.py          # SQL agent logic
│   ├── database.py       # Database connection handling
│   └── config.py         # Configuration management
├── notebooks/            # Jupyter notebooks (Sprint 1)
├── data/                 # Sample databases
├── docs/
│   ├── plans/
│   └── decisions/
├── tests/                # Tests (Sprint 2)
├── requirements.txt
├── PLAN.md
└── README.md
```

## Architecture Notes

- **LangGraph Agent**: State graph with retry logic (max 3 retries on SQL generation failure)
- **State**: `question`, `sql_query`, `result`, `error`, `retry_count`
- **Flow**: generate_sql -> validate_query -> execute_query -> END (with error handling loop)
- **Security consideration**: Prevent destructive queries (INSERT, UPDATE, DELETE) - TBD

## Environment

- **Platform**: WSL Ubuntu on Windows
- **Project path (WSL)**: `/home/berto/sql-query-agent-ollama/`
- **Project path (Windows)**: `\\wsl.localhost\Ubuntu\home\berto\sql-query-agent-ollama\`
- **DSM repository**: `D:\data-science\agentic-ai-data-science-methodology\`
- **Virtual environment**: `venv/` (not yet created)

## Key References

- **DSM Methodology**: `D:\data-science\agentic-ai-data-science-methodology\`
- **DSM 1.0** (notebook work): `DSM_1.0_Data_Science_Collaboration_Methodology_v1.1.md`
- **DSM 4.0** (app development): `DSM_4.0_Software_Engineering_Adaptation_v1.0.md`
- **PM Guidelines**: `DSM_2_0_ProjectManagement_Guidelines_v2_v1.1.md`
- **PLAN.md**: Development roadmap with sprint details and code snippets
