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
| **Default** | `llama3.1:8b` | 4.7GB | Recommended — 100% parsability, zero hallucination, 1.7x faster ([DEC-005](docs/decisions/DEC-005_model-selection-llama3-1-8b.md)) |
| Alternative | `sqlcoder:7b` | 4.1GB | SQL fine-tuned, same accuracy but higher hallucination risk |
| Untested | `mannix/defog-llama3-sqlcoder-8b` | ~4.7GB | Llama 3 SQL fine-tune (candidate for Sprint 2) |
| Untested | `sqlcoder:15b` | ~8GB | Higher accuracy if VRAM allows |

## Project Status

- [x] **Phase 0**: Research state of the art ([findings](docs/research/text_to_sql_state_of_art.md))
- [x] **Sprint 1, Phase 1**: Environment setup — Ollama, models, Chinook database
- [x] **Sprint 1, Phase 2**: Core agent build — 5-node LangGraph agent, SQL post-processing, 6/6 test queries passing
- [x] **Sprint 1, Phase 3**: Evaluation framework — 14-query test suite, 2-model comparison, model selection ([EXP-001](data/experiments/s01_d02_exp001/README.md))
- [ ] **Sprint 2**: Streamlit application

### Evaluation Results (Sprint 1, Phase 3)

EXP-001 compared `sqlcoder:7b` and `llama3.1:8b` on a 14-query test suite (5 Easy, 5 Medium, 4 Hard):

| Metric | sqlcoder:7b | llama3.1:8b |
|--------|-------------|-------------|
| Execution Accuracy | 42.9% (6/14) | 42.9% (6/14) |
| Raw Parsability | 85.7% (12/14) | **100% (14/14)** |
| Table Hallucination | 2 instances | **0 instances** |
| Avg Latency | 30.3s | **17.6s** |

**Key finding:** SQL fine-tuning did not improve accuracy over a general-purpose model at the 7-8B scale. `llama3.1:8b` is recommended for its reliability (zero hallucination, 100% parsability) and speed.

| Difficulty | sqlcoder:7b | llama3.1:8b |
|------------|-------------|-------------|
| Easy (5) | 80% | **100%** |
| Medium (5) | 40% | 20% |
| Hard (4) | 0% | 0% |

See the [full experiment report](data/experiments/s01_d02_exp001/README.md) and [PLAN.md](docs/plans/PLAN.md) for the development roadmap.

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
├── scripts/              # Reusable evaluation scripts
│   └── eval_harness.py   # Evaluation framework (EX, parsability, error categorization)
├── data/
│   ├── chinook.db        # Chinook SQLite sample database (11 tables)
│   └── experiments/      # Experiment artifacts (DSM C.1.6)
│       └── s01_d02_exp001/  # EXP-001: Model comparison
├── docs/
│   ├── plans/            # Sprint plans
│   ├── decisions/        # Decision log (DEC-001 through DEC-005)
│   ├── checkpoints/      # Milestone checkpoints
│   ├── research/         # State-of-art research
│   ├── feedback/         # DSM methodology feedback
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
