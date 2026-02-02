# SQL Query Agent with Ollama

A natural language to SQL query application powered by open-source LLMs running locally via [Ollama](https://ollama.ai/).

## Overview

This project enables users to query SQL databases using plain English. Instead of writing SQL manually, simply ask questions like:

- "How many customers are in each country?"
- "What are the top 5 best-selling products?"
- "Show me all orders from last month with total over $100"

The agent translates your question into SQL, validates it, executes it, and returns the results -- with automatic error correction if the first attempt fails.

**Framing:** This is a text-to-code generation testbed. SQL is a constrained language, making it ideal for systematic evaluation of LLM code generation capabilities before tackling general-purpose code.

## Architecture

The agent uses a **LangGraph state graph** informed by current text-to-SQL research (DIN-SQL, MAC-SQL, CHESS):

```
[schema_filter] -> [generate_sql] -> [validate_query] -> [execute_query] -> [END]
                        ^                  |                    |
                        |                  v                    v
                        +--------- [handle_error] <-----------+
                                   (max 3 retries)
```

Key design decisions:
- **Schema filtering** before generation (most impactful sub-task per research)
- **SQL post-processing** for dialect normalization (ILIKE→LIKE, column casing, PostgreSQL→SQLite)
- **SQL validation** via sqlglot before execution (catches syntax errors without hitting DB)
- **Self-correction** with error context feedback (research shows +5-10% accuracy)
- **Model-aware prompting** (sqlcoder:7b requires specific prompt format; see [DEC-003](docs/decisions/DEC-003_model-aware-prompts.md))
- **Structured graph** over free-form ReAct (better for 7B local models)

## Features

- **Local LLM**: Runs entirely on your machine using Ollama (no API keys needed)
- **Natural Language Interface**: Ask questions in plain English
- **SQL Generation**: Automatically generates and executes SQL queries
- **Schema Awareness**: Understands your database structure for accurate queries
- **Self-Correction**: Retries with error context if SQL generation fails
- **Evaluation Framework**: Systematic model comparison with standardized metrics
- **Streamlit UI**: User-friendly web interface (Sprint 2)

## Tech Stack

- **LLM Runtime**: [Ollama](https://ollama.ai/)
- **Agent Framework**: [LangChain](https://python.langchain.com/) + [LangGraph](https://langchain-ai.github.io/langgraph/)
- **SQL Validation**: [SQLGlot](https://github.com/tobymao/sqlglot)
- **Frontend**: Streamlit (Sprint 2)
- **Database**: SQLite (with potential for PostgreSQL/MySQL support)
- **Language**: Python 3.10+

## Recommended Models

| Priority | Model | Size | Notes |
|----------|-------|------|-------|
| Primary | `sqlcoder:7b` | 4.1GB | Fine-tuned for SQL, outperforms GPT-3.5 |
| Primary | `mannix/defog-llama3-sqlcoder-8b` | ~4.7GB | Llama 3 SQL fine-tune |
| Comparison | `llama3.1:8b` | 4.7GB | General-purpose baseline |
| Optional | `sqlcoder:15b` | ~8GB | Higher accuracy if VRAM allows |

## Project Status

- [x] **Phase 0**: Research state of the art ([findings](docs/research/text_to_sql_state_of_art.md))
- [x] **Sprint 1, Phase 1**: Environment setup — Ollama, models, Chinook database
- [x] **Sprint 1, Phase 2**: Core agent build — 5-node LangGraph agent, SQL post-processing, 6/6 test queries passing
- [ ] **Sprint 1, Phase 3**: Evaluation framework — test suite, metrics, model comparison
- [ ] **Sprint 2**: Streamlit application

### Current Results (Sprint 1, Phase 2)

The agent successfully answers natural language questions about the Chinook database:

| Query | Result | Retries | Time |
|-------|--------|---------|------|
| Top 5 artists by album count | Iron Maiden (21), Led Zeppelin (14), Deep Purple (11)... | 0 | 19.1s |
| List all genres | 20 genres returned | 0 | 5.0s |
| Top 3 customers by spending | Helena Holy ($49.62), Richard Cunningham ($47.62)... | 0 | 20.8s |
| Find all tracks by AC/DC | 8 tracks found | 0 | 8.1s |
| Track count for Heavy Metal/Metal/Blues | 483 tracks | 0 | 18.0s |
| Top 5 artists in Metal/Blues genres | Iron Maiden (132), Metallica (112), Eric Clapton (32)... | 0 | 27.0s |

See [PLAN.md](docs/plans/PLAN.md) for the detailed development roadmap.

## Getting Started

### Prerequisites

1. Install [Ollama](https://ollama.ai/)
2. Pull a model:
   ```bash
   ollama pull sqlcoder:7b
   ```
3. Python 3.10+

### Installation

```bash
# Clone the repository
git clone https://github.com/albertodiazdurana/sql-query-agent-ollama.git
cd sql-query-agent-ollama

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Usage

*Coming soon -- see Sprint 1 notebook for experimentation*

## Project Structure

```
sql-query-agent-ollama/
├── .claude/              # AI agent configuration
├── app/                  # Streamlit application (Sprint 2)
├── notebooks/            # Jupyter notebooks (Sprint 1)
├── data/                 # Sample databases
├── docs/
│   ├── plans/            # Sprint plans
│   ├── decisions/        # Decision log
│   ├── research/         # State-of-art research
│   └── blog/             # Blog materials and drafts
├── tests/                # Tests (Sprint 2)
├── requirements.txt
└── README.md
```

## Evaluation

The project includes a systematic evaluation framework comparing models on:

| Metric | Description |
|--------|-------------|
| Execution Accuracy | Does the query return correct results? |
| Parsability Rate | % of valid SQL on first attempt |
| Retry Rate | How often error correction is needed |
| Latency | Time from question to answer |
| Error Categorization | Schema linking / syntax / logic / hallucination |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
