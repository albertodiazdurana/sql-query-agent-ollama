# SQL Query Agent with Ollama - Development Plan

## Project Overview
Build an application that converts natural language questions into SQL queries using an open-source LLM via Ollama. Framed as a text-to-code generation testbed -- SQL is a constrained language ideal for systematic evaluation before tackling general-purpose code generation.

---

## Technology Assessment

### LangChain
LangChain is well-suited for this project:
- **SQL Database Chain**: Built-in `SQLDatabaseChain` for text-to-SQL
- **SQL Agent**: `create_sql_agent` with tools for schema inspection, query execution, and error handling
- **Ollama Integration**: Native support via `ChatOllama` or `Ollama` classes
- **Prompt Templates**: Easy customization of SQL generation prompts

### LangGraph
LangGraph will be used from Sprint 1 for robust agentic workflows:

**Benefits for this project:**
- Query validation -> retry loops (if SQL fails, regenerate with error context)
- Multi-step reasoning (break complex questions into sub-queries)
- Human-in-the-loop approval before executing queries
- Maintaining conversation state across multiple queries
- Clean separation of concerns (nodes for generation, validation, execution)

**Recommendation:**
- **Sprint 1**: Build LangGraph-based agent in notebook (with schema filtering, validation, retry logic)
- **Sprint 2**: Extend with human-in-the-loop approval in Streamlit UI

### SQLGlot
SQL parser/transpiler for pre-execution validation. Validates SQL syntax and checks that referenced tables/columns exist in the actual schema without hitting the database.

---

## Recommended Ollama Models (Research-Informed)

| Priority | Model | Size | Notes |
|----------|-------|------|-------|
| Primary | `sqlcoder:7b` | 4.1GB | Fine-tuned for SQL, outperforms GPT-3.5 on Defog benchmarks |
| Primary | `mannix/defog-llama3-sqlcoder-8b` | ~4.7GB | Llama 3 fine-tune for SQL |
| Comparison | `llama3.1:8b` | 4.7GB | General-purpose baseline for model comparison |
| Optional | `sqlcoder:15b` | ~8GB | Higher accuracy if VRAM allows |

**Research finding:** Fine-tuned SQL models outperform general-purpose models of the same size by 15-20% on Spider EX. See `docs/research/text_to_sql_state_of_art.md` Section 3.

---

## Sprint 1: Jupyter Notebook Experimentation

### Goals
- Validate the approach and model capabilities with a research-informed architecture
- Systematically compare models using standardized evaluation metrics
- Build a reproducible evaluation framework
- Document findings for blog post

### Tasks

#### 1.0 Research (Completed)
- [x] Survey state of the art in text-to-SQL (benchmarks, approaches, metrics)
- [x] Document findings in `docs/research/text_to_sql_state_of_art.md`
- [x] Identify architectural recommendations for local LLM deployment

#### 1.1 Environment Setup
- [ ] Create virtual environment
- [ ] Install dependencies: `langchain`, `langchain-community`, `langchain-ollama`, `langgraph`, `sqlalchemy`, `sqlglot`, `jupyter`
- [ ] Pull Ollama models: `sqlcoder:7b`, `llama3.1:8b`
- [ ] Verify Ollama connectivity

#### 1.2 Database Setup
- [ ] Create or use a sample SQLite database (e.g., Chinook)
- [ ] Document the schema for reference
- [ ] Prepare sample rows for few-shot prompting

#### 1.3 Core Agent Build (Notebook)
- [ ] Connect to database with SQLAlchemy
- [ ] Initialize Ollama LLM via LangChain (`temperature=0`, `num_ctx=8192`)
- [ ] Implement schema filtering node (prune irrelevant tables before generation)
- [ ] Build LangGraph agent with nodes: `schema_filter`, `generate_sql`, `validate_query` (sqlglot), `execute_query`, `handle_error`
- [ ] Implement retry logic with error context feedback (max 3 retries)
- [ ] Implement SQL post-processing (extract SQL from markdown, remove explanatory text)
- [ ] Implement security: prevent destructive queries via prompt rules + sqlglot validation
- [ ] Tune prompts using research best practices (explicit rules, few-shot examples, no chain-of-thought for 7B)

#### 1.4 Evaluation Framework
- [ ] Design test suite: Easy (4-5), Medium (4-5), Hard (3-5) queries
- [ ] Implement metrics tracking:
  - Execution Accuracy (primary): does the query return correct results?
  - Parsability Rate: % of syntactically valid SQL on first attempt
  - Retry Rate: how often the agent needs error correction
  - Latency: time from question to answer
  - Error Categorization: schema linking / syntax / logic / hallucination
- [ ] Compare at least 2 models (sqlcoder:7b vs llama3.1:8b) on same test suite
- [ ] Document model performance, limitations, and error patterns

### Deliverables
- `notebooks/01_sql_agent_exploration.ipynb`
- Working prototype with documented evaluation results
- Blog materials collected (DSM Section 2.5.6)
- DSM feedback entries logged

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
│   ├── agent.py         # SQL agent logic (from notebook)
│   ├── database.py      # Database connection handling
│   └── config.py        # Configuration management
├── notebooks/
│   └── 01_sql_agent_exploration.ipynb
├── data/
│   └── sample.db        # Sample database
├── docs/
│   ├── plans/
│   ├── decisions/
│   ├── research/
│   └── blog/
├── tests/
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
- Blog post draft (DSM Section 2.5.8)
- DSM feedback files (DSM Section 6.4.5)

---

## LangGraph Agent Architecture (Research-Informed)

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class SQLState(TypedDict):
    question: str
    sql_query: str
    result: str
    error: str | None
    retry_count: int
    filtered_schema: str

# Graph structure (enhanced from DIN-SQL / MAC-SQL patterns):
#
#   [schema_filter] --> [generate_sql] --> [validate_query] --> [execute_query] --> [END]
#                            ^                   |                    |
#                            |                   v                    v
#                            +---------- [handle_error] <-----------+
#                                        (max 3 retries)
#
# Key design decisions (from research):
# - schema_filter: prune irrelevant tables before generation (most impactful sub-task)
# - validate_query: sqlglot parsing + schema validation before execution
# - handle_error: feeds error message + question + failed SQL back (self-correction pattern)
# - Structured graph > free-form ReAct for 7B models
```

### Prompt Template (Optimized for 7B Local Models)
```python
SYSTEM_PROMPT = """You are a SQLite expert. Generate a SELECT query to answer the user's question.

Rules:
- Output ONLY a valid SQLite SELECT statement
- Use only the tables and columns listed in the schema
- Never use INSERT, UPDATE, DELETE, DROP, or ALTER
- Use table aliases for any JOINs
- Add LIMIT 100 unless counting or aggregating"""

USER_PROMPT = """Schema:
{filtered_schema}

{few_shot_examples}

Question: {question}

SQL:"""
```

**Research-based prompting notes:**
- Few-shot examples give 10-20% improvement for 7B models (DAIL-SQL finding)
- Chain-of-thought hurts small models -- use direct generation
- Temperature = 0 always (SQL is deterministic)
- Set `num_ctx=8192` to avoid context window issues
- Post-process to extract SQL from markdown/explanations

---

## Evaluation Metrics

| Metric | Description | Why |
|--------|-------------|-----|
| Execution Accuracy (EX) | Does query return correct results? | Primary metric used by Spider/BIRD |
| Parsability Rate | % of syntactically valid SQL on first attempt | Measures raw model quality |
| Retry Rate | How often agent needs error correction | Measures first-attempt quality |
| Latency | Time from question to answer | Critical for local LLM UX |
| Error Categorization | Schema linking / syntax / logic / hallucination | Identifies improvement areas |

### Test Suite Structure
- **Easy (4-5 queries)**: Single table, simple WHERE, basic aggregation
- **Medium (4-5 queries)**: JOINs, GROUP BY + HAVING, ORDER BY with LIMIT
- **Hard (3-5 queries)**: Multi-table JOINs, subqueries, complex aggregation, string matching

---

## Open Questions (Updated)

1. **Database choice**: Chinook (well-known, good for testing) or custom?
2. **VRAM available**: Determines if we can run sqlcoder:15b or stick with 7B models
3. **Multi-database**: Support only SQLite, or also PostgreSQL/MySQL?

---

## References

- Research document: `docs/research/text_to_sql_state_of_art.md`
- Key papers: DIN-SQL (arXiv:2304.11015), MAC-SQL (arXiv:2312.11242), CHESS (arXiv:2405.16755)
- Benchmarks: [Spider](https://yale-lily.github.io/spider), [BIRD](https://bird-bench.github.io/)
- Tools: [SQLCoder](https://github.com/defog-ai/sqlcoder), [SQLGlot](https://github.com/tobymao/sqlglot)
