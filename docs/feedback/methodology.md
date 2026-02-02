# DSM Feedback: Final Project Methodology

**Project:** SQL Query Agent with Ollama
**Author:** Alberto
**Date:** 2026-02-01 (started, finalized at project end)
**Duration:** Ongoing

---

## 1. Project Overview

| Item | Planned | Actual |
|------|---------|--------|
| **Objective** | NL-to-SQL agent with local LLMs via Ollama | Phase 2 complete, entering Phase 3 |
| **Dataset** | Sample SQLite database (Chinook) | Active — 11 tables, 3,503 tracks |
| **Timeline** | Sprint 1 (notebook) + Sprint 2 (Streamlit) | In progress — Sprint 1, Phase 3 next |
| **Deliverables** | Notebook prototype + Streamlit app + blog | Notebook: 25 cells completed |

---

## 2. Technical Pipeline (What Was Actually Built)

*To be documented as each phase completes.*

### Phase 0: Research
- Surveyed text-to-SQL state of the art (benchmarks, approaches, models)
- Output: `docs/research/text_to_sql_state_of_art.md`
- Key findings: schema filtering most impactful, sqlglot for pre-validation, few-shot +10-20% for 7B models, structured graph > ReAct for small models

### Phase 1: Environment & Database Setup
- **Approach:** Verify all infrastructure before writing agent code. Each step validated in the notebook with printed output before proceeding.
- **Steps completed:**
  1. Created SQLAlchemy engine for `data/chinook.db` (SQLite)
  2. Inspected all 11 tables: columns, types, PKs, FKs (Cell 3)
  3. Verified row counts across all tables (Cell 4) — largest table: PlaylistTrack (8,715 rows)
  4. Verified Ollama connectivity from WSL via gateway IP `172.27.64.1:11434` (Cell 5)
  5. Pulled `sqlcoder:7b` (3.8 GB) and `llama3.1:8b` (4.6 GB) on Windows host
  6. Tested both models with a simple prompt (Cell 6) — confirmed responses
  7. Extracted 3 sample rows from 6 key tables for few-shot prompt embedding (Cell 7)
- **Findings:**
  - First-call latency is high (sqlcoder 31.9s, llama3.1 10.9s) due to Ollama model loading; subsequent calls much faster
  - sqlcoder:7b responded with hallucinated SQL to a simple echo test; llama3.1:8b responded correctly. This foreshadowed the prompt format issue discovered in Phase 2.
- **Outcome:** All Phase 1 success criteria met — Ollama responds, database loads, 2+ models available

### Phase 2: Core Agent Build — Complete
- **Approach:** Build each LangGraph node as an independent function, test individually with print-based tracing, then wire into graph. This isolates bugs before they compound in the full pipeline.
- **Architecture:** 5-node LangGraph StateGraph: `schema_filter` → `generate_sql` → `validate_query` → `execute_query` → `handle_error` (retry loop), plus SQL post-processing layer
- **Steps completed:**
  1. Defined `AgentState` TypedDict with 10 fields: question, relevant_tables, schema_text, generated_sql, is_valid, validation_error, results, error, retry_count, model_name (Cell 9)
  2. **schema_filter (Cell 10):** Keyword-based table selection — matches question words against table/column names, scores and ranks, selects top 5 + FK-connected tables. Tested: "How many albums does each artist have?" → correctly selected Album + Artist (2/11 tables, 219-char schema)
  3. **generate_sql (Cells 11-13):** Initial generic prompt produced empty responses from sqlcoder:7b. Diagnosed in Cell 12 by testing both prompt formats side-by-side. Revised to model-aware routing: sqlcoder gets `### Task / ### Database Schema / ### Answer` format, others get generic instruction format. Both models now generate valid SQL.
  4. **validate_query (Cell 14):** Two-stage validation — (a) security check blocks INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE, (b) sqlglot parses SQL for syntax errors. Tested all three paths: valid passes, DROP blocked, bad syntax caught with line/column info.
  5. **execute_query (Cell 15):** Runs validated SQL against SQLite via SQLAlchemy, returns up to 20 rows. Captures execution errors (e.g., wrong column names) without crashing.
  6. **handle_error (Cell 16):** Feeds error context back to LLM with model-aware repair prompt. Increments retry_count for loop control (max 3). Tested: sqlcoder successfully repaired `SELECT Foo FROM Artist` into valid SQL.
  7. **LangGraph wiring (Cell 17):** State graph compiled with conditional edges — validation routes to execute or retry, execution routes to retry or END.
  8. **End-to-end testing (Cells 18-19):** First run: 1/3 queries passed, 2 failed (column casing + ILIKE). Identified need for post-processing.
  9. **Prompt improvement attempt (Cells 20-21):** Added SQLite-specific rules to prompts. Retested — still failed. Confirmed prompt rules cannot override fine-tuned model behavior.
  10. **SQL post-processing (Cells 22-24, DEC-004):** Built programmatic fix for three SQLite incompatibilities: ILIKE→LIKE, NULLS LAST removal, snake_case→PascalCase column mapping. Retested — both previously failed queries now pass with 0 retries.
  11. **Genre exploration (Cell 25):** Tested agent on multi-table JOIN queries about Heavy Metal/Metal/Blues genres. Both pass with 0 retries, including a 3-table JOIN with correlated EXISTS subquery.
- **Key findings:**
  - sqlcoder:7b is prompt-format-sensitive — empty output with generic prompts, correct output with its native format (DEC-003)
  - llama3.1:8b produces more complete SQL (includes JOINs for readable output) but is 3-4x slower
  - sqlcoder:7b generates PostgreSQL-style SQL (ILIKE, NULLS LAST, snake_case columns); prompt rules don't override training (DEC-004)
  - Retry loop cannot fix systematic model biases — post-processing is the correct pattern for dialect normalization
  - Error repair works but is slow (~62s for sqlcoder repair calls)
- **Outcome:** All Phase 2 success criteria met — 6/6 queries pass end-to-end, retry loop tested, validation catches errors, destructive queries blocked

### Phase 3: Evaluation Framework
*Pending*

---

## 3. Libraries & Tools

| Library | Version | Purpose |
|---------|---------|---------|
| langchain | TBD | LLM orchestration |
| langchain-ollama | TBD | Ollama integration |
| langgraph | TBD | Agent state graph |
| sqlalchemy | TBD | Database connectivity |
| sqlglot | TBD | SQL validation pre-execution |
| jupyter | TBD | Notebook experimentation |
| streamlit | TBD | Web UI (Sprint 2) |

---

## 4. Final Results

*To be completed at project end.*

---

## 5. Project Structure (Final)

*To be documented at project end.*

---

## 6. Plan vs Reality

| Aspect | Planned | Actual | Delta |
|--------|---------|--------|-------|
| *To be filled as project progresses* | | | |

---

## 7. Methodology Observations for DSM

*To be populated throughout the project. Initial observations:*

1. Adding a research phase before sprint planning significantly improved architecture decisions for this ML/AI project.
2. DSM_0 checklist was effective for project initialization -- provided clear structure without unnecessary overhead.

---

## 8. DSM Section Scoring

*Migrated from standalone Validation Tracker per DSM v1.3.19 (BACKLOG-041).*

### Sections Used

| DSM Section | Sprint/Day | Times Used | Avg Score | Top Issue |
|-------------|------------|------------|-----------|-----------|
| DSM_0 (Start Here Guide) | S1 Setup | 1 | 4.0 | None |
| PM Guidelines (Templates 1, 4, 7) | S1 Setup | 1 | 4.0 | None |
| Section 6.4.5 + Appendix E.12 | S1 Setup | 1 | 3.0 | Naming/purpose overlap |
| PM Guidelines Template 5 (Checkpoints) | S1 Setup | 1 | 3.5 | Missing from project structure |
| Custom Instructions + 6.2.5/7.1 | S1 Phase 1 | 1 | 2.5 | Notebook collaboration undocumented |
| PM Guidelines + Section 6.4.1 | S1 Phase 2 | 1 | 2.5 | No intra-sprint documentation cadence |

### Entry 1: DSM_0 (Start Here Guide)
- **Date:** 2026-02-01 | **Sprint:** S1 Setup | **Type:** Success
- **Context:** Initializing project repository structure, CLAUDE.md, plans, and dependencies
- **Finding:** DSM_0 provided a clear checklist for project setup. The sequence was logical and thorough.
- **Scores:** Clarity 4, Applicability 4, Completeness 4, Efficiency 4 (Avg: 4.0)
- **Recommendation:** Add a "research/literature review" step to DSM_0 for projects that benefit from surveying state of the art before planning.

### Entry 2: PM Guidelines (Templates 1, 4, 7)
- **Date:** 2026-02-01 | **Sprint:** S1 Setup | **Type:** Success
- **Context:** Creating Sprint 1 detailed plan with phases, priorities, and success criteria
- **Finding:** Templates provided good structure. Combined elements from multiple templates to fit a sprint-level plan.
- **Scores:** Clarity 4, Applicability 4, Completeness 4, Efficiency 4 (Avg: 4.0)
- **Recommendation:** A sprint-level template (not just daily) would be a useful addition to PM Guidelines.

### Entry 3: Section 6.4.5 + Appendix E.12 (Feedback/Validation)
- **Date:** 2026-02-01 | **Sprint:** S1 Setup | **Type:** Pain Point
- **Context:** Setting up feedback tracking files for the project
- **Finding:** The Validation Tracker (E.12) and feedback files (6.4.5) overlap significantly. The naming ("validation" vs "feedback") doesn't clarify the distinction.
- **Scores:** Clarity 2, Applicability 3, Completeness 4, Efficiency 3 (Avg: 3.0)
- **Recommendation:** Consolidate or clearly differentiate. See `backlogs.md` for detailed proposal.

### Entry 4: PM Guidelines Template 5 (Checkpoints)
- **Date:** 2026-02-01 | **Sprint:** S1 Setup | **Type:** Gap
- **Context:** Creating first milestone checkpoint after project setup
- **Finding:** Template 5 specifies `docs/checkpoints/` but DSM_0 project structure template does not include it. Projects discover the gap when reaching Section 6.4.1.
- **Scores:** Clarity 4, Applicability 4, Completeness 3, Efficiency 3 (Avg: 3.5)
- **Recommendation:** Add `docs/checkpoints/` to DSM_0 project structure template.

### Entry 5: Custom Instructions + 6.2.5/7.1 (Notebook Protocol)
- **Date:** 2026-02-01 | **Sprint:** S1 Phase 1 | **Type:** Gap
- **Context:** Starting notebook work for Sprint 1. Needed to establish AI-human collaboration protocol for Jupyter cells.
- **Finding:** Custom Instructions did not describe the notebook cell-by-cell collaboration protocol. The agent attempted to write .ipynb directly. Sections 6.2.5 and 7.1 describe the principle but not the interaction mechanics.
- **Scores:** Clarity 2, Applicability 2, Completeness 2, Efficiency 4 (Avg: 2.5)
- **Recommendation:** Add "Notebook Collaboration Protocol" to Custom Instructions specifying: agent provides cells as code blocks, user pastes and executes, user shares output, agent validates before next cell.

### Entry 6: PM Guidelines + Section 6.4.1 (Intra-Sprint Documentation Cadence)
- **Date:** 2026-02-02 | **Sprint:** S1 Phase 2 | **Type:** Gap
- **Context:** After completing Phase 1 and building all Phase 2 nodes, we realized no documentation had been created since the setup checkpoint. The sprint plan had no documentation steps at phase boundaries, and the DSM only mandates checkpoints at sprint boundaries.
- **Finding:** Intra-sprint phase transitions are natural documentation milestones but neither the DSM nor the sprint plan template prompts the user to document at these points. We created the Phase 1 checkpoint retroactively during Phase 2, losing the clean transition record.
- **Scores:** Clarity 3, Applicability 2, Completeness 2, Efficiency 3 (Avg: 2.5)
- **Recommendation:** (1) Add "Phase Boundary Checklist" to sprint plan template with documentation steps. (2) Clarify in Section 6.4.1 that checkpoints should occur at significant intra-sprint milestones, not only at sprint end. See `backlogs.md` for full proposal.

### Summary Metrics

| Metric | Value |
|--------|-------|
| Entries logged | 6 |
| Average score | 3.2 / 5 |
| Gaps found | 3 |
| Pain points | 1 |
| Successes | 2 |

### Project-Specific DSM Adaptations
1. Added Phase 0 (Research) before standard DSM_0 setup steps -- surveyed text-to-SQL state of the art to inform architecture and model selection
2. Combined PM Guidelines Templates 1 (task breakdown), 4 (prerequisites), and 7 (MUST/SHOULD/COULD) into a single sprint plan format
