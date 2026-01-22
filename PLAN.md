# SQL Query Agent with Ollama - Development Plan

## Project Overview
Build an application that converts natural language questions into SQL queries using an open-source LLM via Ollama.

---

## Technology Assessment

### LangChain - Recommended ✅
LangChain is well-suited for this project:
- **SQL Database Chain**: Built-in `SQLDatabaseChain` for text-to-SQL
- **SQL Agent**: `create_sql_agent` with tools for schema inspection, query execution, and error handling
- **Ollama Integration**: Native support via `ChatOllama` or `Ollama` classes
- **Prompt Templates**: Easy customization of SQL generation prompts

### LangGraph - Recommended ✅
LangGraph will be used from Sprint 1 for robust agentic workflows:

**Benefits for this project:**
- Query validation → retry loops (if SQL fails, regenerate with error context)
- Multi-step reasoning (break complex questions into sub-queries)
- Human-in-the-loop approval before executing queries
- Maintaining conversation state across multiple queries
- Clean separation of concerns (nodes for generation, validation, execution)

**Recommendation:**
- **Sprint 1**: Build LangGraph-based agent in notebook (with retry logic)
- **Sprint 2**: Extend with human-in-the-loop approval in Streamlit UI

---

## Sprint 1: Jupyter Notebook Experimentation

### Goals
- Validate the approach and model capabilities
- Experiment with different prompts and configurations
- Test with a sample database

### Tasks

#### 1.1 Environment Setup
- [ ] Create virtual environment
- [ ] Install dependencies: `langchain`, `langchain-community`, `langchain-ollama`, `langgraph`, `sqlalchemy`, `jupyter`
- [ ] Pull an Ollama model (suggested: `llama3.1`, `mistral`, or `codellama`)

#### 1.2 Database Setup
- [ ] Create or use a sample SQLite database (e.g., Chinook, Northwind, or custom)
- [ ] Document the schema for reference

#### 1.3 Core Experimentation (Notebook)
- [ ] Connect to database with SQLAlchemy
- [ ] Initialize Ollama LLM via LangChain
- [ ] Test basic SQL generation with `SQLDatabase` + `SQLDatabaseChain`
- [ ] Build LangGraph agent with nodes: `generate_sql`, `validate_query`, `execute_query`, `handle_error`
- [ ] Implement retry logic for failed SQL generation
- [ ] Test edge cases: joins, aggregations, ambiguous queries
- [ ] Tune prompts for better SQL generation

#### 1.4 Evaluation
- [ ] Test with 10-15 sample natural language queries
- [ ] Document model performance and limitations
- [ ] Identify which Ollama model works best

### Deliverables
- `notebooks/01_sql_agent_exploration.ipynb`
- Working prototype with documented findings

---

## Sprint 2: Streamlit Application

### Goals
- Build a user-friendly web interface
- Add production-ready features
- Handle errors gracefully

### Tasks

#### 2.1 Project Structure
```
sql-query-agent-ollama/
├── app/
│   ├── __init__.py
│   ├── main.py          # Streamlit entry point
│   ├── agent.py         # SQL agent logic
│   ├── database.py      # Database connection handling
│   └── config.py        # Configuration management
├── notebooks/
│   └── 01_sql_agent_exploration.ipynb
├── data/
│   └── sample.db        # Sample database
├── requirements.txt
├── README.md
└── PLAN.md
```

#### 2.2 Core Features
- [ ] Database connection interface (upload SQLite or provide connection string)
- [ ] Natural language input box
- [ ] Generated SQL display (with syntax highlighting)
- [ ] Query results table
- [ ] Query history sidebar

#### 2.3 Enhanced Features (Optional)
- [ ] Schema viewer/explorer
- [ ] "Explain this query" feature
- [ ] Export results to CSV
- [ ] Model selection dropdown (switch Ollama models)
- [ ] Query approval step before execution (LangGraph opportunity)

#### 2.4 Error Handling
- [ ] Invalid SQL recovery (retry with error context)
- [ ] Database connection error handling
- [ ] Ollama availability check

### Deliverables
- Functional Streamlit app
- Updated README with usage instructions

---

## Suggested Ollama Models

| Model | Size | Best For |
|-------|------|----------|
| `llama3.1:8b` | 4.7GB | Good balance of speed and quality |
| `codellama:13b` | 7.4GB | Code-focused, better SQL syntax |
| `mistral:7b` | 4.1GB | Fast, decent SQL generation |
| `sqlcoder:7b` | 4.1GB | Specialized for SQL (if available) |

---

## Sample Code Snippets

### Basic LangChain SQL Agent Setup
```python
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_ollama import ChatOllama

# Initialize
db = SQLDatabase.from_uri("sqlite:///data/sample.db")
llm = ChatOllama(model="llama3.1:8b", temperature=0)

# Create agent
agent = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)

# Query
response = agent.invoke({"input": "How many customers are in each country?"})
```

### LangGraph SQL Agent Architecture
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class SQLState(TypedDict):
    question: str
    sql_query: str
    result: str
    error: str | None
    retry_count: int

# Graph structure:
#
#   [generate_sql] --> [validate_query] --> [execute_query] --> [END]
#         ^                   |                    |
#         |                   v                    v
#         +-------- [handle_error] <---------------+
#
# Conditional edges:
# - validate_query: if invalid SQL → handle_error, else → execute_query
# - execute_query: if error → handle_error, else → END
# - handle_error: if retry_count < 3 → generate_sql, else → END (with error)
```

---

## Open Questions for Review

1. **Database choice**: Do you have an existing database to use, or should we create a sample one?
2. **Model preference**: Any specific Ollama model you want to prioritize?
3. **Security**: Should the app prevent destructive queries (INSERT, UPDATE, DELETE)?
4. **Multi-database**: Support only SQLite, or also PostgreSQL/MySQL?

---

## Next Steps

1. Review and approve this plan
2. Set up the development environment
3. Begin Sprint 1 with the Jupyter notebook
