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
[schema_filter] → [generate_sql] → [postprocess_query] → [validate_query] → [execute_query] → [END]
                        ^                                       |                    |
                        |                                       v                    v
                        +-------------------------------- [handle_error] <-----------+
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
- **Streamlit UI**: User-friendly web interface with schema explorer

## Tech Stack

- **LLM Runtime**: [Ollama](https://ollama.ai/)
- **Agent Framework**: [LangChain](https://python.langchain.com/) + [LangGraph](https://langchain-ai.github.io/langgraph/)
- **SQL Validation**: [SQLGlot](https://github.com/tobymao/sqlglot)
- **Frontend**: [Streamlit](https://streamlit.io/)
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
- [x] **Sprint 2, Phase 1**: Code extraction — `app/` modules, 33 pytest tests
- [x] **Sprint 2, Phase 2**: Ablation study — 84 experiments, zero-shot best ([EXP-002](data/experiments/s02_ablation/README.md))
- [x] **Sprint 2, Phase 3**: Streamlit UI — schema explorer, query history, error handling
- [x] **Sprint 2, Phase 4**: Docker support — `docker-compose up` runs everything

### EXP-001: Model Comparison (Sprint 1, Phase 3)

EXP-001 compared `sqlcoder:7b` (SQL-specialized fine-tune) against `llama3.1:8b` (general-purpose) using a hypothesis-driven approach with pre-defined rejection criteria.

**Hypotheses tested:**
- **H1:** SQL fine-tuning yields higher Execution Accuracy (research predicts +15-20%) — **Rejected** (equal EX)
- **H2:** General-purpose model produces more readable SQL — **Partially confirmed**
- **H3:** Fine-tuned model needs more dialect post-processing — **Inconclusive** (measurement limitation)

**Test suite:** 14 queries across 3 difficulty tiers, each with pre-computed ground truth:
- **Easy (5):** Single table, simple WHERE, basic aggregation (e.g., "How many employees are there?")
- **Medium (5):** JOINs, GROUP BY + HAVING, ORDER BY + LIMIT (e.g., "Which genre has the most tracks?")
- **Hard (4):** Multi-table JOINs, subqueries, complex aggregation (e.g., "Find customers who have never purchased a Jazz track")

**Results:**

| Metric | sqlcoder:7b | llama3.1:8b |
|--------|-------------|-------------|
| Execution Accuracy | 42.9% (6/14) | 42.9% (6/14) |
| Raw Parsability | 85.7% (12/14) | **100% (14/14)** |
| Effective Parsability | 64.3% (9/14) | **92.9% (13/14)** |
| Table Hallucination | 2 instances | **0 instances** |
| Avg Latency | 30.3s | **17.6s** |

| Difficulty | sqlcoder:7b | llama3.1:8b |
|------------|-------------|-------------|
| Easy (5) | 80% | **100%** |
| Medium (5) | 40% | 20% |
| Hard (4) | 0% | 0% |

**Error analysis:** Failures were categorized using a 6-category hierarchy (schema linking → syntax → dialect → hallucination → logic → unknown). sqlcoder:7b's failures were diverse (hallucination, runtime, dialect), while llama3.1:8b's were predominantly logic errors — a more predictable failure mode.

**Key finding:** SQL fine-tuning did not improve accuracy over a general-purpose model at the 7-8B scale. `llama3.1:8b` is recommended for its reliability (zero hallucination, 100% parsability) and speed. See [DEC-005](docs/decisions/DEC-005_model-selection-llama3-1-8b.md).

**Limitations discovered (6):** Each experiment produces a structured limitation registry (LIM-001 through LIM-006), tracking severity, type, and disposition. Key limitations include 0% Hard query accuracy (LIM-001), table hallucination in sqlcoder (LIM-002), and no few-shot examples in prompts (LIM-006). These feed directly into Sprint 2's improvement backlog.

See the [full experiment report](data/experiments/s01_d02_exp001/README.md) for per-query results, error pattern analysis, and evaluation design decisions.

### EXP-002: Ablation Study (Sprint 2, Phase 2)

EXP-002 tested 6 prompt configurations (3 prompt types × 2 schema types) across 14 queries — 84 total experimental runs.

**Configurations tested:**
- **Prompt types:** zero-shot, few-shot (2 examples), chain-of-thought
- **Schema types:** full (all 11 tables), selective (keyword-filtered)

**Results:**

| Configuration | Execution Accuracy | Syntax Valid | Avg Latency |
|--------------|-------------------|--------------|-------------|
| **zero_shot_full** | **50% (7/14)** | 100% | 8.97s |
| zero_shot_selective | 43% (6/14) | 93% | 12.17s |
| few_shot_full | 36% (5/14) | 100% | 8.46s |
| few_shot_selective | 43% (6/14) | 100% | 11.54s |
| cot_full | 29% (4/14) | 93% | 7.78s |
| cot_selective | 43% (6/14) | 100% | 11.37s |

**Key findings:**
1. **Few-shot examples hurt:** Adding examples *reduced* accuracy by 14pp (50% → 36%)
2. **Chain-of-thought hurt:** CoT was the worst performer at 29%
3. **Full schema wins:** Despite more "noise," full context beat selective filtering
4. **Baseline improved:** 50% EX vs 42.9% EXP-001 baseline (+7.1pp)

**Recommendation:** Use zero-shot prompting with full schema for llama3.1:8b. This contradicts common prompt engineering assumptions — empirical validation matters.

See the [full ablation report](data/experiments/s02_ablation/README.md) for detailed analysis.

## Getting Started

### Prerequisites

1. Install [Ollama](https://ollama.ai/)
2. Pull the recommended model (~5GB):
   ```bash
   ollama pull llama3.1:8b
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

#### Option 1: Run Locally (Recommended for Development)

1. **Start Ollama** (in a separate terminal):
   ```bash
   ollama serve
   ```

2. **Pull the model** (first time only, ~5GB download):
   ```bash
   ollama pull llama3.1:8b
   ```

3. **Run the Streamlit app**:
   ```bash
   PYTHONPATH=. streamlit run app/main.py
   ```

4. **Open your browser** at http://localhost:8501

#### Option 2: Run with Docker (Recommended for Deployment)

Docker Compose runs both the app and Ollama together — no manual setup needed.

```bash
# Start everything (first run downloads the model)
docker-compose up

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

Open http://localhost:8501 in your browser.

**GPU Support (NVIDIA):** Uncomment the `deploy` section in `docker-compose.yml` for faster inference.

#### Using the App

1. The sidebar shows **Ollama status** (green = connected) and a **Schema Explorer** with table relationships
2. Type a natural language question in the main area, e.g., "How many employees are there?"
3. Click **Run Query** to see the generated SQL and results
4. Query history is saved in the sidebar

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
│       ├── s01_d02_exp001/  # EXP-001: Model comparison
│       └── s02_ablation/    # EXP-002: Prompt ablation study
├── docs/
│   ├── plans/            # Sprint plans
│   ├── decisions/        # Decision log (DEC-001 through DEC-008)
│   ├── checkpoints/      # Milestone checkpoints (7 total)
│   ├── research/         # State-of-art research
│   ├── feedback/         # DSM methodology feedback (22 entries)
│   └── blog/             # Blog posts, LinkedIn posts, images
├── tests/                # Unit tests (pytest)
├── requirements.txt
└── README.md
```

## Testing

Run the test suite with:

```bash
PYTHONPATH=. pytest tests/ -v
```

The test suite (33 tests) covers:
- **`test_database.py`** — Schema introspection, column map building, SQL post-processing
- **`test_agent.py`** — Query validation, routing logic, schema filtering, security (blocked keywords)

## Evaluation Framework

The project uses a systematic, hypothesis-driven evaluation approach adapted from the [Spider benchmark](https://yale-lily.github.io/spider) methodology. Each experiment follows a structured template:

1. **Hypotheses** defined before testing, with explicit rejection criteria
2. **Curated test suite** organized by difficulty (Easy / Medium / Hard), with pre-computed ground truth
3. **6 quantitative metrics** tracked per model per query
4. **Structured error categorization** classifying failures into actionable categories
5. **Limitation discovery** producing a numbered registry (LIM-###) that feeds into the next sprint's backlog

### Metrics

| Metric | Description |
|--------|-------------|
| Execution Accuracy (EX) | Does the query return correct results? (adapted from Spider EX) |
| Raw Parsability | % of syntactically valid SQL before post-processing |
| Effective Parsability | % of valid SQL after post-processing, on first attempt |
| Retry Rate | How often the self-correction loop is needed |
| Post-Processing Rate | % of queries needing dialect normalization |
| Latency | Time from question to answer |

### Error Categories

Failures are classified using a priority-ordered hierarchy — more specific categories take precedence:

| Category | Definition | Actionable fix |
|----------|------------|----------------|
| Schema linking | Wrong table or column referenced | Better schema filtering |
| Syntax | Invalid SQL that fails parsing | Prompt engineering |
| Dialect | PostgreSQL syntax in SQLite context | Post-processing rules |
| Hallucination | References non-existent tables/columns | Schema-aware validation |
| Logic | Valid SQL, executes, but wrong results | Few-shot examples, reasoning |
| Unknown | None of the above | Manual analysis |

### Reproducibility

Experiments are fully reproducible via scripts:

```bash
# Run evaluation for a specific model
python data/experiments/s01_d02_exp001/run_experiment.py llama3.1:8b

# Results saved as JSON with per-query metrics
```

The evaluation harness ([`scripts/eval_harness.py`](scripts/eval_harness.py)) is model-agnostic and reusable across experiments. Experiment artifacts (runner scripts, result JSONs, documentation) follow a consistent folder structure under `data/experiments/`.

## Development Methodology

This project is one of two active case studies for the [Data Science Methodology (DSM)](https://github.com/albertodiazdurana/agentic-ai-data-science-methodology), a structured collaboration framework for AI-assisted data science and software engineering projects. Both repositories are developed in parallel by the same author: DSM defines the methodology, while this project and the [DSM Graph Explorer](https://github.com/albertodiazdurana/agentic-ai-data-science-methodology) validate it in practice. The relationship is bidirectional — DSM provides the structure for sprint planning, experiment design, and decision-making, and this project feeds real-world observations back into DSM through dedicated feedback files (`docs/feedback/`), creating a continuous improvement loop between methodology and application.

DSM shapes how this project is organized:

- **Decision log** ([`docs/decisions/`](docs/decisions/)) — Numbered records (DEC-001 through DEC-008) capturing architectural choices with context, alternatives considered, and rationale. Decisions are referenced throughout the codebase.
- **Experiment templates** — Each evaluation follows a structured template with pre-defined hypotheses, rejection criteria, metrics, and limitation discovery (see [EXP-001](data/experiments/s01_d02_exp001/README.md)).
- **Limitation registries** — Experiments produce numbered limitations (LIM-###) with severity and disposition, feeding directly into the next sprint's backlog.
- **Sprint boundary checklists** — Checkpoints ([`docs/checkpoints/`](docs/checkpoints/)), methodology feedback ([`docs/feedback/`](docs/feedback/)), and blog materials ([`docs/blog/`](docs/blog/)) are produced at each sprint boundary.
- **Methodology feedback loop** — The project feeds observations back to DSM itself via `docs/feedback/methodology.md` and `docs/feedback/backlogs.md`, improving the methodology for future projects.

The project uses **DSM 1.0** (Data Science Collaboration) for Sprint 1 notebook experimentation and **DSM 4.0** (Software Engineering Adaptation) for Sprint 2 application development.

## Blog

- **Part 1:** [Two Experiments in Parallel: Building a Text-to-SQL Agent While Testing a Collaboration Methodology](docs/blog/blog-s01.md) — From notebook exploration to structured evaluation. Covers the research-driven architecture, model comparison (sqlcoder vs llama3.1), and what we learned from running two experiments at once.
- **Part 2:** [The Case for Human-Agent Collaboration: What 28 Test Outputs Taught Me About Cognitive Limits](docs/blog/blog-s02-collaboration-value.md) — Why structured human-AI workflows catch errors that automation misses.
- **Part 3:** [What 84 Experiments Taught Me About Prompt Engineering — When Best Practices Don't Transfer](docs/blog/blog-s02-ablation.md) — Counter-intuitive ablation study findings (few-shot and CoT hurt performance).
- **Part 4:** *Ready to write* — "Shipping a Local-First AI App" — From notebook prototype to Docker-deployed application.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
