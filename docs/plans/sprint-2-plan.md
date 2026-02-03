# Sprint 2 Plan: Streamlit Application

**Project:** SQL Query Agent with Ollama
**Sprint:** 2 of 2
**DSM Track:** DSM 4.0 (Software Engineering Adaptation)
**Author:** Alberto
**Status:** In Progress

---

## Purpose

Build a Streamlit web application from the Sprint 1 notebook prototype. Extract agent code into modular Python packages, address key accuracy limitations (LIM-003, LIM-006), add a user-friendly interface, and write tests.

## Workflow

**Changed from Sprint 1:** Claude Code writes files directly (no paste protocol). User reviews in IDE. Tests run to verify.

---

## Inputs from Sprint 1

| Input | Source | Status |
|-------|--------|--------|
| Working agent (5 nodes, graph wiring) | Notebook cells 9-17, 22-24 | Extract to `app/agent.py` |
| Database setup (schema, sample rows) | Notebook cells 1-7 | Extract to `app/database.py` |
| Configuration (Ollama URL, prompts, models) | Notebook cells, run_experiment.py | Extract to `app/config.py` |
| Post-processing (ILIKE, NULLS LAST, column casing) | Notebook cells 22-24 | Move to own graph node (LIM-003) |
| Evaluation harness | `scripts/eval_harness.py` | Reuse as-is |
| Experiment runner | `data/experiments/s01_d02_exp001/run_experiment.py` | Reference for code structure |
| Model recommendation | DEC-005: llama3.1:8b default | Apply in config |
| 6 limitations | LIM-001 through LIM-006 | Address LIM-003, LIM-006 |

---

## Phases

### Phase 1: Code Extraction & Architecture (Execution mode: script)

**Objective:** Extract notebook code into clean Python modules with tests.

**Files to create:**

1. **`app/__init__.py`** — Package marker
2. **`app/config.py`** — All configuration:
   - Ollama URL, default model (llama3.1:8b), temperature, num_ctx, max_retries
   - Prompt templates (GENERIC_PROMPT, SQLCODER_PROMPT, ERROR_REPAIR_GENERIC, ERROR_REPAIR_SQLCODER)
   - Security constants (BLOCKED_KEYWORDS)
   - DB defaults
3. **`app/database.py`** — Database layer:
   - `create_db_engine(db_path)` — SQLAlchemy engine creation
   - `get_schema_info(engine)` — Full schema introspection (tables, columns, PKs, FKs)
   - `get_sample_rows(engine, tables, n=3)` — Sample rows for few-shot
   - `build_column_map(schema_info)` — PascalCase column mapping
   - `postprocess_sql(sql, column_map)` — ILIKE/NULLS/casing fixes
4. **`app/agent.py`** — Agent logic:
   - `AgentState` TypedDict
   - 5+1 node functions: `schema_filter`, `generate_sql`, **`postprocess_query`** (NEW — LIM-003), `validate_query`, `execute_query`, `handle_error`
   - Routing functions: `check_validation`, `should_retry`
   - `build_agent(engine, model_name)` — Constructs and compiles the graph
   - **Key change (LIM-003):** Post-processing becomes its own graph node between `generate_sql` and `validate_query`, so raw SQL is captured in state before post-processing. This fixes the metrics reliability issue.
5. **`tests/test_database.py`** — pytest tests for database module
6. **`tests/test_agent.py`** — pytest tests for agent module (mock LLM calls)
7. **`tests/conftest.py`** — Shared fixtures (test engine, sample schema)

**New graph structure:**
```
[schema_filter] → [generate_sql] → [postprocess_query] → [validate_query] → [execute_query] → [END]
                        ^                                       |                    |
                        |                                       v                    v
                        +-------------------------------- [handle_error] <-----------+
```

**Readiness for Phase 2:**
- [ ] All 4 app/ modules created and importable
- [ ] `build_agent()` compiles a working graph
- [ ] pytest tests pass for database and agent modules
- [ ] Post-processing is a separate graph node (LIM-003 resolved)

---

### Phase 2: Ablation Study & Evaluation Rigor (Execution mode: script)

**Objective:** Systematic ablation study to measure the impact of prompt engineering choices. Demonstrates reproducible ML experiments and evaluation pipelines that support fast iteration.

**Ablation Matrix:**

| Experiment | Variable | Values | Runs |
|------------|----------|--------|------|
| E1: Prompt Structure | Template | Zero-shot (baseline), Few-shot, Chain-of-thought | 3 × 14 = 42 |
| E2: Few-shot Selection | Example count | 0, 2, 3 examples | 3 × 14 = 42 |
| E3: Schema Context | Context amount | Full schema, Selective (relevant tables only) | 2 × 14 = 28 |

**Total runs:** ~112 (with overlap reduction: ~56 unique configurations)

**Activities:**
1. **Prompt variants in config.py:**
   - `ZERO_SHOT_PROMPT` (current baseline)
   - `FEW_SHOT_PROMPT` (2-3 static examples from Sprint 1 test set)
   - `COT_PROMPT` (chain-of-thought: reasoning before SQL)
2. **Schema context variants:**
   - Full schema (current)
   - Selective schema (filter to question-relevant tables)
3. **Ablation runner script:** `scripts/run_ablation.py`
   - Iterates over prompt × schema × example configurations
   - Logs all results to `data/experiments/s02_ablation/`
   - Produces comparison table
4. **Metrics tracked:**
   - Execution Accuracy (EX) — primary
   - Syntax Validity (VV) — secondary
   - Latency (ms) — informational
5. **Document as EXP-002** with ablation findings and best configuration

**Key files:**
- `app/config.py` — prompt variants
- `scripts/run_ablation.py` — ablation experiment runner
- `data/experiments/s02_ablation/` — results folder

**Readiness for Phase 3:**
- [ ] Prompt variants implemented (zero-shot, few-shot, CoT)
- [ ] Schema context variants implemented (full, selective)
- [ ] Ablation runner script working
- [ ] All ablation runs complete with results logged
- [ ] Best configuration identified (EX improvement over baseline)
- [ ] EXP-002 documented with comparison table

---

### Phase 3: Streamlit UI (Execution mode: script)

**Objective:** Build the web interface with core features.

**File:** `app/main.py` — Streamlit entry point

**Core features (MUST):**
1. **Natural language input** — Text box for questions
2. **SQL display** — Show generated SQL with syntax highlighting (`st.code`)
3. **Results table** — Display query results as `st.dataframe`
4. **Error display** — Show retry attempts, error messages, recovery status
5. **Ollama status check** — Verify Ollama is running on app start
6. **Database selector** — Default to bundled Chinook, allow SQLite file upload via `st.file_uploader`

**Layout:**
- Sidebar: database selector, model info, query history
- Main area: input box, SQL output, results table

**Readiness for Phase 4:**
- [ ] App runs with `streamlit run app/main.py`
- [ ] User can ask a question and see SQL + results
- [ ] Error states handled gracefully (Ollama down, bad SQL, empty results)
- [ ] Query history maintained in session state

---

### Phase 4: Enhanced Features & Polish (Execution mode: script)

**Objective:** Add SHOULD/COULD features, final testing, documentation.

**SHOULD features:**
1. **Model selection dropdown** — Switch between available Ollama models
2. **Schema viewer** — Expandable sidebar showing tables/columns/types
3. **CSV export** — Download results as CSV via `st.download_button`

**COULD features:**
4. **Query approval step** — Show SQL before executing, user clicks "Run" (human-in-the-loop)
5. **"Explain this query"** — Use LLM to explain the generated SQL in plain English
6. **Query editing** — Let user modify generated SQL before execution

**Documentation:**
- Update README with usage instructions, screenshots
- Update PLAN.md Sprint 2 status
- Sprint boundary checklist: checkpoint, feedback, decisions, blog materials, README
- Blog materials for Sprint 2

---

## Priority Breakdown

### MUST
- [x] Extract notebook code into `app/` modules (config, database, agent) ✓ Phase 1
- [x] Separate post-processing into own graph node (LIM-003) ✓ Phase 1
- [x] pytest tests for database and agent modules ✓ Phase 1
- [ ] Ablation study: prompt variants (zero-shot, few-shot, CoT)
- [ ] Ablation study: schema context variants (full, selective)
- [ ] Ablation runner script with reproducible experiment logging
- [ ] Streamlit UI with NL input → SQL → results flow
- [ ] Ollama availability check
- [ ] Database selector (Chinook default + SQLite upload)
- [ ] Error handling (SQL errors, connection errors, Ollama down)

### SHOULD
- [ ] Model selection dropdown
- [ ] Schema viewer in sidebar
- [ ] CSV export
- [ ] Query history in sidebar
- [ ] EXP-002 documentation with ablation comparison table

### COULD
- [ ] Query approval before execution (human-in-the-loop)
- [ ] "Explain this query" feature
- [ ] Query editing (modify generated SQL)
- [ ] Streamlit Cloud deployment config

---

## Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| App functional | NL → SQL → results via Streamlit | Manual testing |
| Ablation complete | All 3 experiments run (prompt, few-shot, schema) | Results in `s02_ablation/` |
| Agent accuracy | >= Sprint 1 baseline (42.9% EX) | Best ablation config |
| Ablation impact | Identify best prompt configuration | Comparison table |
| Test coverage | pytest tests for database + agent modules | `pytest tests/` passes |
| Error handling | Graceful handling of 3 error types | Manual testing |
| Reproducibility | All experiments logged with config + results | Experiment artifacts |

---

## Key Files

| File | Purpose | Phase |
|------|---------|-------|
| `app/__init__.py` | Package marker | 1 |
| `app/config.py` | Configuration, prompts, constants | 1, 2 |
| `app/database.py` | DB engine, schema, post-processing | 1 |
| `app/agent.py` | AgentState, nodes, graph builder | 1 |
| `app/main.py` | Streamlit entry point | 3 |
| `scripts/run_ablation.py` | Ablation experiment runner | 2 |
| `data/experiments/s02_ablation/` | Ablation results folder | 2 |
| `docs/research/ablation-study-design.md` | Research findings on ablation methodology | 2 |
| `tests/conftest.py` | Shared test fixtures | 1 |
| `tests/test_database.py` | Database module tests | 1 |
| `tests/test_agent.py` | Agent module tests | 1 |

---

## Verification

1. **Phase 1:** `python -c "from app.agent import build_agent; print('OK')"` + `pytest tests/`
2. **Phase 2:** `python scripts/run_ablation.py` — runs all ablation experiments, outputs comparison table
3. **Phase 3:** `streamlit run app/main.py` — ask "How many employees are there?" and verify answer (8)
4. **Phase 4:** Test all UI features manually, run full pytest suite
