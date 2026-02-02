# Sprint 1 Plan: Notebook Experimentation

**Project:** SQL Query Agent with Ollama
**Sprint:** 1 of 2
**DSM Track:** DSM 1.0 (Data Science Collaboration)
**Author:** Alberto
**Status:** Complete

---

## Purpose

Build a working text-to-SQL agent prototype in a Jupyter notebook using LangGraph and Ollama, with a systematic evaluation framework comparing at least two models. The notebook serves as the experimentation ground before extracting code into the Streamlit app (Sprint 2).

---

## Inputs & Dependencies

| Input | Status | Notes |
|-------|--------|-------|
| Ollama installed and running | Done | Running on Windows host, accessible via WSL gateway IP |
| `sqlcoder:7b` model pulled | Done | 3.8 GB |
| `llama3.1:8b` model pulled | Done | 4.6 GB |
| Sample SQLite database (Chinook) | Done | `data/chinook.db`, 11 tables |
| Python venv with dependencies | Done | `requirements.txt` installed |
| Research document | Done | `docs/research/text_to_sql_state_of_art.md` |

---

## Phases

### Phase 1: Environment & Database Setup

**Objective:** Verify Ollama connectivity, set up sample database, document schema.

**Activities:**
- Verify Ollama is running and accessible from WSL
- Pull models: `sqlcoder:7b`, `llama3.1:8b`
- Download or create Chinook SQLite database in `data/`
- Connect to database with SQLAlchemy, inspect schema
- Document schema (tables, columns, relationships) in notebook
- Prepare sample rows for few-shot prompting

**Deliverables:**
- Ollama models available locally
- `data/chinook.db` (or equivalent sample database)
- Notebook section: database setup and schema documentation

**Readiness for Phase 2:**
- [x] Ollama responds to test prompt
- [x] Database loads and schema is inspectable via SQLAlchemy
- [x] At least 2 models pulled and verified

---

### Phase 2: Core Agent Build

**Objective:** Build the LangGraph agent with schema filtering, SQL generation, validation, execution, and error handling.

**Activities:**
- Initialize Ollama LLM via `ChatOllama` (`temperature=0`, `num_ctx=8192`)
- Define `SQLState` TypedDict (question, sql_query, result, error, retry_count, filtered_schema)
- Implement nodes:
  - `schema_filter`: prune irrelevant tables based on question
  - `generate_sql`: prompt LLM with filtered schema + few-shot examples
  - `validate_query`: sqlglot parsing + check referenced tables/columns exist
  - `execute_query`: run validated SQL against database
  - `handle_error`: feed error context back for retry (max 3)
- Build LangGraph `StateGraph` with conditional edges (validation pass/fail, execution success/error)
- Implement SQL post-processing (extract SQL from markdown, strip explanatory text)
- Implement security rules: block INSERT, UPDATE, DELETE, DROP, ALTER via prompt + sqlglot
- Tune prompts: explicit rules, few-shot examples, no chain-of-thought (research finding for 7B models)

**Deliverables:**
- Working agent that takes a natural language question and returns SQL results
- Notebook section: agent architecture with inline documentation

**Readiness for Phase 3:**
- [x] Agent successfully answers at least 3 simple queries end-to-end
- [x] Retry logic triggers on intentionally malformed scenarios
- [x] sqlglot validation catches syntax errors before execution
- [x] Destructive queries are blocked

---

### Phase 3: Evaluation Framework

**Objective:** Systematically compare models using standardized metrics and a curated test suite.

**Activities:**
- Design test suite by difficulty:
  - **Easy (4-5 queries):** single table, simple WHERE, basic aggregation
  - **Medium (4-5 queries):** JOINs, GROUP BY + HAVING, ORDER BY with LIMIT
  - **Hard (3-5 queries):** multi-table JOINs, subqueries, complex aggregation, string matching
- Define ground-truth expected results for each query
- Implement metrics collection:
  - Execution Accuracy (EX): does the query return correct results?
  - Parsability Rate: % of syntactically valid SQL on first attempt
  - Retry Rate: how often the agent needs error correction
  - Latency: time from question to answer
  - Error Categorization: schema linking / syntax / logic / hallucination
- Run full test suite on `sqlcoder:7b` and `llama3.1:8b`
- Analyze results: per-model breakdown, per-difficulty breakdown, error patterns
- Document findings, limitations, and recommendations

**Deliverables:**
- Evaluation results table in notebook
- Model comparison analysis with error pattern insights
- Notebook section: evaluation framework and results

**Readiness for Sprint 2:**
- [x] At least 2 models evaluated on same test suite
- [x] Results documented with metrics tables
- [x] Best-performing model identified for Sprint 2 default (llama3.1:8b — DEC-005)
- [x] Known limitations documented (6 limitations, LIM-001 through LIM-006)

---

## Priority Breakdown (MUST / SHOULD / COULD)

### MUST (Non-negotiable) — All Met
- [x] Working LangGraph agent with generate -> validate -> execute -> error loop
- [x] Schema filtering node (research: most impactful sub-task)
- [x] sqlglot validation before execution
- [x] Security: block destructive SQL
- [x] Evaluation on at least 2 models with Execution Accuracy metric
- [x] Test suite with Easy + Medium queries (minimum 8 queries)

### SHOULD (Expected if on track) — 3/4 Met
- [x] Hard queries in test suite (4 queries)
- [x] All 5 evaluation metrics tracked (EX, Parsability, Retry Rate, Latency, Error Categories) — plus Post-Processing Rate (6 total)
- [ ] Few-shot examples in prompts (research: +10-20% for 7B) — **deferred to Sprint 2 (LIM-006)**
- [x] Blog materials collected throughout sprint

### COULD (Bonus) — Not Done
- [ ] Test `mannix/defog-llama3-sqlcoder-8b` as third model
- [ ] Test `sqlcoder:15b` if VRAM allows
- [ ] Visualization of evaluation results (charts/plots)
- [ ] Experiment with different prompt variations

---

## Success Criteria

| Criterion | Target | Result | Status |
|-----------|--------|--------|--------|
| Agent functional | End-to-end NL -> SQL -> results | 6/6 Phase 2 queries pass | **Met** |
| Execution Accuracy (best model) | >= 60% on full test suite | 42.9% (both models) | **Not met** |
| Parsability Rate | >= 70% first-attempt valid SQL | 100% (llama3.1:8b) | **Met** |
| Models compared | >= 2 models on same test suite | 2 models, 14 queries each | **Met** |
| Test coverage | >= 8 queries across difficulties | 14 queries (3 difficulties) | **Met** |
| Error handling | Retry loop works on failures | Tested and functional | **Met** |

---

## Deliverables Summary

| Deliverable | Location | Status |
|-------------|----------|--------|
| Exploration notebook | `notebooks/01_sql_agent_exploration.ipynb` | Complete (32 cells) |
| Sample database | `data/chinook.db` | Complete |
| Evaluation harness | `scripts/eval_harness.py` | Complete |
| Experiment results | `data/experiments/s01_d02_exp001/` | Complete (2 JSON, README, runner) |
| Blog materials | `docs/blog/` | Complete |
| DSM feedback files | `docs/feedback/` | Complete (11 entries, 10 backlog proposals) |
| Decision log | `docs/decisions/DEC-001` through `DEC-005` | Complete |

---

## Open Decisions (Resolved)

1. **Database choice:** Chinook — DEC-001
2. **VRAM budget:** 7-8B models only (sqlcoder:7b, llama3.1:8b). 15B not tested.
3. **Few-shot selection:** Deferred to Sprint 2 (LIM-006). No few-shot in Sprint 1.
