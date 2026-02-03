# DSM Feedback: Final Project Methodology

**Project:** SQL Query Agent with Ollama
**Author:** Alberto
**Date:** 2026-02-01 (started, finalized at project end)
**Duration:** Ongoing

---

## 1. Project Overview

| Item | Planned | Actual |
|------|---------|--------|
| **Objective** | NL-to-SQL agent with local LLMs via Ollama | Sprint 1 complete — agent built, evaluated, model selected |
| **Dataset** | Sample SQLite database (Chinook) | Active — 11 tables, 3,503 tracks |
| **Timeline** | Sprint 1 (notebook) + Sprint 2 (Streamlit) | Sprint 1 complete — ready for Sprint 2 |
| **Deliverables** | Notebook prototype + Streamlit app + blog | Notebook: 32 cells, eval scripts, EXP-001 results |

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

### Phase 3: Evaluation Framework — Complete
- **Approach:** Used DSM experiment framework (C.1.3, C.1.5, C.1.6) to structure model comparison. Design work (test suite, ground truth) done in notebook; execution work (evaluation harness, model runs) extracted to scripts after first run. Analysis (results loading, comparison tables, findings) returned to notebook.
- **Steps completed:**
  1. Designed 14-query test suite across 3 difficulty levels (5 Easy, 5 Medium, 4 Hard) — Cell 27
  2. Pre-computed ground truth for all 14 queries using direct SQL execution
  3. Built evaluation harness with 6 quantitative metrics: Execution Accuracy (EX), Raw Parsability, Effective Parsability, Retry Rate, Post-Processing Rate, Latency — extracted to `scripts/eval_harness.py`
  4. Implemented Spider EX-inspired comparison with flexible 3-mode matching (exact, set, subset) — ED-2
  5. Implemented error categorization with priority hierarchy (schema→syntax→dialect→hallucination→logic→unknown) — ED-3
  6. Ran sqlcoder:7b evaluation (14 queries, ~7 min) — initially in notebook, saved to JSON
  7. Extracted runner to `data/experiments/s01_d02_exp001/run_experiment.py` (per C.1.6 artifact organization)
  8. Ran llama3.1:8b evaluation via script — results saved to JSON automatically
  9. Loaded and compared results in notebook (Cell 29): summary tables, per-difficulty breakdowns
  10. Per-query analysis (Cell 30): divergences, error category distribution, latency by difficulty, shared failures
  11. Hypothesis evaluation (Cell 31): H1 REJECTED (equal EX), H2 PARTIALLY CONFIRMED (parsability), H3 INCONCLUSIVE (ED-1 risk)
  12. Limitation discovery per C.1.5 (Cell 32): 6 limitations documented (LIM-001 through LIM-006)
  13. Updated EXP-001 README with full quantitative/qualitative results, findings, limitations
  14. Model recommendation: llama3.1:8b as Sprint 2 default (DEC-005)
- **Key findings:**
  - Both models: 42.9% EX (6/14), below the 60% sprint target
  - llama3.1:8b: 100% parsability, 0 hallucination, 1.7x faster — recommended for Sprint 2
  - sqlcoder:7b: hallucinated 2 tables (`payment`, `invoiceintrack`), 2 runtime failures on hard queries
  - Both models: 0% Hard accuracy — fundamental limitation at 7-8B parameter scale
  - Post-processing metrics unreliable due to ED-1 (post-processing inside `generate_sql` node) — LIM-003
  - Notebook-to-script transition should have happened before Cell 28, not after — led to DSM feedback entry
- **Outcome:** EXP-001 complete. Model selected (DEC-005). 6 limitations documented for Sprint 2 backlog. Sprint 1 evaluation framework functional and reusable via `scripts/eval_harness.py`.

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
| Custom Instructions + 6.2.5/7.1 | S1 Phase 1, S1 Phase 3 | 2 | 2.6 | Notebook collaboration undocumented; cell numbering too broad |
| PM Guidelines + Section 6.4.1 | S1 Phase 2 | 1 | 2.5 | No intra-sprint documentation cadence |
| Appendix C.1 + 5.2.1 + DSM 4.0 §4.4 | S1 Phase 3 | 1 | 3.75 | Not referenced by project workflow |
| Custom Instructions + C.1.3 + 5.2.1 | S1 Phase 3 | 1 | 2.25 | No decision traceability or citation requirements |
| Sprint Plan Template + Custom Instructions | S1 Phase 3 | 1 | 2.5 | No guidance on notebook-to-script transition point |
| CLAUDE.md / DSM Workflow | S1 Sprint Boundary | 1 | 3.0 | README update missing from sprint boundary checklist |
| Section 6.4.5 (Feedback Deliverables) | S1 Sprint Boundary | 1 | 2.75 | Blog materials grouped with DSM feedback — wrong location |
| Section 2.5.6 (Blog Deliverable Process) | S1 Sprint Boundary | 1 | 2.75 | No naming convention for blog artifacts (materials vs draft vs post) |

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

### Entry 7: Appendix C.1 + Section 5.2.1 + DSM 4.0 §4.4 (Experiment Framework)
- **Date:** 2026-02-02 | **Sprint:** S1 Phase 3 | **Type:** Gap
- **Context:** Entering Phase 3 (Evaluation Framework). The sprint plan defined evaluation activities from scratch — test suite design, metrics collection, model comparison. Neither the plan nor the AI agent referenced DSM's experiment framework. The user explicitly directed the agent to check DSM for experiment guidance.
- **Finding:** DSM has a comprehensive, well-designed experiment framework spanning five sections: C.1.3 (Capability Experiment Template — exactly our model comparison use case), C.1.5 (Limitation Discovery Protocol — LIM-### format for documenting model limitations), C.1.6 (Experiment Artifact Organization — folder structure and registry), 5.2.1 (Experiment Tracking — parameter and metric logging), and DSM 4.0 §4.4 (Tests vs Experiments — our evaluation is an experiment, not a test). All five sections are directly applicable. However, the standard project workflow (DSM_0 → Custom Instructions → sprint planning) never references these sections. They exist in Appendix C (Tier 2) and are easy to miss entirely.
- **Scores:** Clarity 4, Applicability 5, Completeness 4, Efficiency 2 (Avg: 3.75)
- **Reasoning:** Clarity 4 — the templates are well-structured and immediately usable. Applicability 5 — perfect fit for our model comparison (both quantitative metrics and qualitative observations). Completeness 4 — covers experiment design, execution, results, limitations, and artifact organization. Efficiency 2 — the framework nearly went unused because nothing in the project workflow triggers its discovery; the user had to catch this gap manually.
- **Recommendation:** Add a "Phase-to-DSM-Section Mapping" to Custom Instructions or sprint plan templates that connects evaluation/experiment phases to Appendix C.1, Section 5.2.1, and DSM 4.0 §4.4. See `backlogs.md` for full proposal.

### Entry 8: Custom Instructions — Notebook Cell Numbering Granularity
- **Date:** 2026-02-02 | **Sprint:** S1 Phase 3 | **Type:** Pain Point
- **Context:** Providing the first Phase 3 markdown cell (experiment header). The project's CLAUDE.md notebook protocol rule stated: "Number each cell with a comment (`# Cell 1`, `# Cell 2`)." The agent followed this rule literally and added `# Cell 26` as the first line of a markdown cell.
- **Finding:** The cell numbering rule was too broad — it didn't distinguish between code cells and markdown cells. Markdown cells serve as structural headers (e.g., `## Phase 3: Evaluation Framework`). Prefixing them with `# Cell 26` adds noise, conflicts with the markdown heading hierarchy, and serves no purpose since markdown cells don't need to be referenced by number in output validation. The user had to manually remove the numbering and correct the protocol. This is a refinement of Entry 5's notebook protocol gap: even after the protocol was established, insufficient granularity in the rules caused agent errors.
- **Scores:** Clarity 3, Applicability 3, Completeness 2, Efficiency 3 (Avg: 2.75)
- **Reasoning:** Clarity 3 — the rule was clear but failed to make a necessary distinction. Applicability 3 — cell numbering is useful for code cells but harmful for markdown cells. Completeness 2 — the protocol omitted the code-vs-markdown distinction entirely. Efficiency 3 — the fix was quick (one CLAUDE.md edit) but required user intervention to catch.
- **Recommendation:** When DSM adopts the Notebook Collaboration Protocol (see Entry 5, backlogs.md), the cell numbering rule should specify: "Number code cells with a comment (`# Cell N`); markdown cells are structural headers and should NOT be numbered." This distinction should be explicit in any protocol documentation.

### Entry 9: Custom Instructions — Decision Traceability and Citation Requirements
- **Date:** 2026-02-02 | **Sprint:** S1 Phase 3 | **Type:** Gap
- **Context:** The agent provided Cell 28 (evaluation harness) — a substantial code cell containing three design decisions (streaming vs. state modification, comparison strategy, error categorization hierarchy) and referencing external concepts (Spider benchmark EX metric, LangGraph streaming API, sqlglot). The agent delivered the code without documenting these decisions or citing the external references. The user had to explicitly remind the agent: "Make sure we are documenting all decisions so that the chain of analysis is traceable. Whenever we are referring to external references we should keep a citations log."
- **Finding:** Neither the Custom Instructions nor CLAUDE.md instruct the agent to proactively document design decisions made during implementation or to maintain a citations log for external references. The DSM's experiment framework (C.1.3) requires structured documentation of experiment design, but does not explicitly require traceability of implementation-level decisions within cells. Section 5.2.1 (Experiment Tracking) covers parameter logging but not decision rationale. As a result, the agent treated Cell 28 as a pure code delivery — technically correct but missing the documentation layer that makes the analysis chain reproducible and auditable. This is the third instance in Phase 3 where the user had to catch a documentation gap (after the experiment framework and cell numbering incidents).
- **Scores:** Clarity 2, Applicability 2, Completeness 2, Efficiency 3 (Avg: 2.25)
- **Reasoning:** Clarity 2 — no guidance exists for when to document implementation decisions vs. project-level decisions. Applicability 2 — DSM has decision records (DEC-###) for project-level decisions but no equivalent for experiment-level or implementation-level decisions. Completeness 2 — citations/references section exists in C.1.3 template but only for the experiment overall, not for individual cells or design choices within the experiment. Efficiency 3 — once prompted, the documentation was straightforward (ED-1 through ED-3 + citations section added to README).
- **Recommendation:** Two additions to the DSM workflow: (1) **Custom Instructions:** Add a rule: "When implementing code that involves design choices (alternative approaches considered, external concepts adapted, non-obvious trade-offs), document the decision rationale before or alongside the implementation. Do not deliver code without documenting the reasoning chain." (2) **C.1.3 Experiment Template or Section 5.2.1:** Add a "Design Decisions" section for implementation-level decisions within experiments (distinct from project-level DEC-### records), and a "Citations" requirement for any external benchmarks, APIs, or tools referenced in the experiment code. See `backlogs.md` for full proposal.

### Entry 10: Sprint Plan Template + Custom Instructions — Notebook-to-Script Transition Point
- **Date:** 2026-02-02 | **Sprint:** S1 Phase 3 | **Type:** Gap
- **Context:** Phase 3 evaluation work was implemented entirely in notebook cells (Cells 26-29). Cell 28 was a ~150-line evaluation harness; Cell 29 ran a full 14-query model evaluation taking ~7 minutes. After the first successful run, the user and agent agreed that long-running evaluation code belongs in scripts, not notebook cells, due to: (a) no checkpointing — a kernel crash loses all results, (b) namespace fragility — notebook variable scope makes code fragile (e.g., Cell 28b fix for `graph` vs `agent`), (c) reproducibility — scripts can be run from CLI without notebook state. The user observed: "In the future we should have identified moving to working in scripts in Cell 28."
- **Finding:** Neither the sprint plan template nor the Custom Instructions provide guidance on **when** to transition from notebook cells to scripts within a notebook-based sprint. The sprint plan defines phases (Setup, Agent Build, Evaluation) but doesn't distinguish between "design work" (best in notebooks — interactive, visual, cell-by-cell validation) and "execution work" (best in scripts — long-running, reproducible, checkpointable). The transition point is the boundary between defining what to evaluate (test suite, ground truth — stays in notebook) and running the evaluation (harness, model execution — should be scripts). This pattern is generalizable: any notebook phase that shifts from exploration/design to computation/execution should trigger a script extraction.
- **Root cause:** The DSM Notebook Collaboration Protocol (Custom Instructions + CLAUDE.md) defines how to work *within* notebooks but not when to *leave* them. The sprint plan template defines phases by *objective* (what to build) but not by *execution mode* (notebook vs script). There is no trigger that says: "When the next cell will be a long-running computation, extract to a script first."
- **What happened:** Cells 28-29 were written, run, and debugged in the notebook. Cell 28b was a runtime fix for a namespace issue (`graph` vs `agent`) that would not have occurred in a standalone script. The evaluation took ~7 minutes in the notebook with no ability to checkpoint or resume. After completion, the code was retroactively extracted to `scripts/eval_harness.py` and `scripts/run_experiment.py`. The llama3.1:8b evaluation will run via script. The correct approach would have been to extract to scripts *before* the first run, not after.
- **Scores:** Clarity 2, Applicability 3, Completeness 2, Efficiency 3 (Avg: 2.5)
- **Reasoning:** Clarity 2 — no guidance exists for this transition. Applicability 3 — the notebook protocol works well for interactive work but doesn't address its own limits. Completeness 2 — the protocol covers notebook collaboration thoroughly but has a blind spot about when notebooks stop being the right tool. Efficiency 3 — the retroactive extraction worked, but we lost time debugging a namespace issue (Cell 28b) that scripts avoid entirely.
- **Recommendation:** Two additions: (1) **Sprint Plan Template:** When defining phases, add a column or note: "Execution mode: notebook / script / both." Phases with long-running computation, batch evaluation, or reproducibility requirements should be flagged for script execution from the start. (2) **Custom Instructions / Notebook Protocol:** Add a transition rule: "When the next step involves long-running computation (>2 minutes), batch processing, or generating results that must be persisted independently, extract the code to a script. The notebook should call the script or load its output, not replicate the computation." See `backlogs.md` for full proposal.

### Entry 11: CLAUDE.md / DSM Workflow — Sprint Boundary Checklist Missing README Update
- **Date:** 2026-02-02 | **Sprint:** S1 Sprint Boundary | **Type:** Gap
- **Context:** At the end of Sprint 1, the sprint boundary checklist (CLAUDE.md: "Follow the sprint boundary checklist: checkpoint, feedback files, decision log, blog entry") was used to enumerate documentation tasks. The repository README — the project's primary public-facing document — was not on the list. The README contained Phase 2 results but not Phase 3 (evaluation) results, the model recommendation, or the updated project structure (scripts, experiment artifacts). The user caught this gap and noted that the README should be part of the checklist.
- **Finding:** The sprint boundary checklist covers internal documentation (checkpoint, feedback, decisions, blog) but omits the external-facing summary. The README is the first thing a reader sees and should always reflect the project's current state. At sprint boundaries, the README typically needs updates to: project status/progress, current results, project structure (if new folders were added), and any changed recommendations (e.g., model selection). Without an explicit checklist item, the README gets stale and out of sync with the documented progress.
- **Scores:** Clarity 3, Applicability 4, Completeness 2, Efficiency 3 (Avg: 3.0)
- **Reasoning:** Clarity 3 — the checklist is clear but incomplete. Applicability 4 — every project has a README that needs updating at sprint boundaries. Completeness 2 — the omission is straightforward but impactful: the README was the only project artifact not covered by the checklist. Efficiency 3 — easy to fix (one line addition) but required user intervention to catch.
- **Recommendation:** Add "Update repository README" to the sprint boundary checklist in CLAUDE.md template, Custom Instructions, and any DSM workflow documentation that defines sprint completion activities. The README update should include: project status, latest results summary, updated project structure, and any changed recommendations. See `backlogs.md` for proposal.

### Entry 12: DSM Feedback Structure — Blog Materials Location Ambiguity
- **Date:** 2026-02-02 | **Sprint:** S1 Sprint Boundary | **Type:** Pain Point
- **Context:** During project setup, blog tracking was placed in `docs/feedback/blog.md` alongside `methodology.md` and `backlogs.md`. DSM Section 6.4.5 groups three feedback deliverables (methodology, backlogs, blog), and the CLAUDE.md project structure mirrored this grouping by putting all three files in `docs/feedback/`. However, blog materials (collected screenshots, narrative angles, material tracking, draft structure) are a project deliverable, not DSM methodology feedback. The `methodology.md` and `backlogs.md` files are about the DSM itself; the blog file is about the project's technical content.
- **Finding:** DSM Section 6.4.5 lists blog tracking as a "feedback deliverable" alongside methodology assessment and backlog proposals. This grouping conflates two different concerns: (1) feedback *about the DSM* (methodology.md, backlogs.md) and (2) a project *output* that happens to be tracked during execution (blog materials). The project structure naturally separates these — `docs/feedback/` for DSM feedback, `docs/blog/` for blog content — but the DSM's grouping of all three as "feedback files" led to the blog tracker being placed in the wrong directory.
- **Scores:** Clarity 3, Applicability 3, Completeness 3, Efficiency 2 (Avg: 2.75)
- **Reasoning:** Clarity 3 — the section groups three deliverables logically by "end of sprint" timing but not by purpose. Applicability 3 — the guidance applies but creates a file organization problem. Completeness 3 — the blog workflow itself (2.5.6-2.5.8) is good. Efficiency 2 — the file had to be moved mid-sprint, and the confusion about where it belongs slowed down sprint boundary documentation.
- **Recommendation:** In DSM Section 6.4.5, distinguish between "DSM feedback files" (methodology.md, backlogs.md — go in `docs/feedback/`) and "project deliverable trackers" (blog materials — go in `docs/blog/`). The sprint boundary checklist should reference both locations. See `backlogs.md` for proposal.

### Entry 13: DSM Blog Workflow — No Naming Convention for Blog Artifacts
- **Date:** 2026-02-02 | **Sprint:** S1 Sprint Boundary | **Type:** Gap
- **Context:** The blog materials file was initially named `blog.md`. At sprint boundary, we realized this name doesn't scale: the `docs/blog/` folder will eventually contain materials files (collected during sprints), blog drafts (written from materials), and final posts (publication-ready). With a single `blog.md` name, there's no way to distinguish between these artifact types or between sprints/phases.
- **Finding:** DSM Section 2.5.6 defines the blog deliverable process (collect → outline → draft → review → finalize → publish) but does not specify a naming convention for the artifacts produced at each step. The file structure in `docs/blog/` needs to accommodate: (1) materials collected during work (`blog-materials-{scope}.md`), (2) the drafted blog post (`blog-{scope}.md`), and (3) the final publishable post (`post-{scope}.md`), where `{scope}` is a sprint/phase identifier like `s01` or `s01-phase3`. Without a convention, the first file gets a generic name that blocks the subsequent files.
- **Scores:** Clarity 2, Applicability 4, Completeness 2, Efficiency 3 (Avg: 2.75)
- **Reasoning:** Clarity 2 — no naming guidance exists for blog artifacts. Applicability 4 — every project following the blog workflow will hit this. Completeness 2 — the 6-step process is well-defined but the file naming for each step's output is not. Efficiency 3 — easy to fix once identified, but required mid-sprint rename.
- **Recommendation:** Add a blog artifact naming convention to Section 2.5.6 or DSM_0 project structure: `blog-materials-{scope}.md` for collected materials, `blog-{scope}.md` for the draft, `post-{scope}.md` for the final publication. The `{scope}` should follow the project's sprint/phase convention (e.g., `s01`, `s01-phase3`, `final`). See `backlogs.md` for proposal.

### Entry 14: DSM 4.0 / Custom Instructions — IDE Permission Mode for Human-in-the-Loop File Edits
- **Date:** 2026-02-02 | **Sprint:** S2 Phase 1 | **Type:** Gap
- **Context:** Sprint 2 moved from the notebook paste protocol (human copies each cell) to Claude Code writing files directly. The CLAUDE.md protocol was updated to specify "explain why → write file → user reviews in IDE." However, the VSCode extension's `initialPermissionMode` setting was set to `acceptEdits`, which auto-applies all file changes without showing a diff approval dialog. The human saw diffs in the chat output but had no approve/reject button — changes were already applied. This silently bypassed the human-in-the-loop principle.
- **Finding:** DSM 4.0 defines the module development protocol (explain → build → confirm → test) and Custom Instructions specify the collaboration workflow, but neither mentions IDE-level permission settings. When the AI agent writes files directly, the IDE's permission configuration determines whether the human actually gets to approve changes before they're applied. The setting `"claudeCode.initialPermissionMode": "default"` enables the diff approval flow; `"acceptEdits"` disables it. This is an environment dependency that affects the entire collaboration model.
- **Scores:** Clarity 2, Applicability 4, Completeness 2, Efficiency 3 (Avg: 2.75)
- **Reasoning:** Clarity 2 — DSM never mentions IDE permission settings. Applicability 4 — every project using Claude Code's direct file writing will face this. Completeness 2 — the collaboration model assumes human review but doesn't ensure the tooling enforces it. Efficiency 3 — quick fix once identified, but the silent bypass went unnoticed through several file writes.
- **Recommendation:** Add IDE permission configuration to DSM 4.0's environment setup phase (P0) and to the Custom Instructions template. Specifically: when using Claude Code in VSCode, set `"claudeCode.initialPermissionMode": "default"` to enable diff approval. This should be listed alongside other environment prerequisites (Python version, venv, dependencies). See `backlogs.md` for proposal.

### Entry 15: Section 2.5.6 / 2.5.7 — Blog Writing Workflow and Emerging Style Guide
- **Date:** 2026-02-03 | **Sprint:** S2 Phase 1 | **Type:** Success + Gap
- **Context:** Wrote the Sprint 1 blog post (`docs/blog/blog-s01.md`) and LinkedIn distribution post collaboratively. The full 6-step process from Section 2.5.6 was completed for the first time: collect materials → structure outline → write draft → review and iterate → finalize → publish (LinkedIn post + blog article).
- **Finding:** The 2.5.6 process works. Having materials collected throughout Sprint 1 (15 items tracked in `blog-materials-s01.md`) made drafting fast — the outline practically wrote itself. The draft went through 5 iterative passes, each addressing one concern: (1) narrative flow, (2) citations/references, (3) challenges section, (4) alignment with target audience, (5) style matching against previous blog post. This incremental refinement produced a polished result.
  - **What's missing from DSM:** Section 2.5.6 defines the *process* but not the *style conventions*. After two blog posts, a consistent style is emerging that should be documented:
    - **Long-form (blog):** Author byline with date. Opening hook with surprising finding. Educational tone (learner sharing discoveries, not authority). Numbered references [1] with full citation list. Tables for metrics. ASCII diagrams for architecture. Closing engagement question. GitHub links at end.
    - **Short-form (LinkedIn):** No emojis, clean line breaks. Opens with counter-intuitive result. Contrasts expectation vs reality. Frames as learning journey. Blog link in first comment (not post body — LinkedIn algorithm deprioritizes external links). Hashtags at end. Image: authentic screenshot preferred over polished graphics.
  - **What's missing from DSM:** Section 2.5.7 (Publication Strategy) mentions "short post + article" but doesn't describe the LinkedIn-specific patterns (link-in-comments, image strategy, hashtag conventions) that are critical for reach.
  - **What worked well:** Using a previous post as a style reference produced consistency. The "alignment exercise" (mapping blog content to a target audience's interests) surfaced implicit angles that strengthened the post without feeling forced.
- **Scores:** Clarity 3, Applicability 4, Completeness 3, Efficiency 4 (Avg: 3.5)
- **Reasoning:** Clarity 3 — the 6-step process is clear but style conventions are undocumented. Applicability 4 — the process worked well for a real blog post. Completeness 3 — covers the writing process but not the format/style layer or platform-specific distribution patterns. Efficiency 4 — the materials-first approach made the whole workflow smooth; the iterative passes were natural, not wasteful.
- **Recommendation:** (1) Add a "Blog Style Guide" subsection to Section 2.5.6 or as a new Section 2.5.9, documenting the long-form and short-form conventions that emerge from each project. The style guide should be a living document — updated after each post, not prescribed upfront. (2) Expand Section 2.5.7 (Publication Strategy) with platform-specific patterns: LinkedIn link-in-comments, image strategy, hashtag conventions. (3) Add "previous post style reference" as a step in the writing process — consistency across posts matters for personal brand. See `backlogs.md` for proposal.

### Entry 16: Blog Workflow — Second Post and LinkedIn Comment Strategy
- **Date:** 2026-02-03 | **Sprint:** S2 Phase 1 | **Type:** Success
- **Context:** Wrote a second blog post (`docs/blog/blog-s02-collaboration-value.md`) on human-agent collaboration value, plus LinkedIn post and comment. This extended the workflow established in Entry 15 with: (a) web research to ground claims in published data (code review fatigue, Fagan inspection metrics), (b) concrete error examples from experiment outputs as visual evidence, (c) LinkedIn comment strategy to promote DSM separately from the main post.
- **Finding:** The workflow from Entry 15 scaled well to a second post. New patterns emerged:
  - **Research integration:** Using WebSearch to find published metrics (defect detection rates, inspection efficiency) added credibility and grounded the blog's claims in external evidence.
  - **Error examples as visuals:** Pulling specific failed outputs from experiment JSON (H4 unit conversion, H2 type mismatch, M5 absurd revenue) created compelling "spot the error" content that illustrates the cognitive limits argument.
  - **LinkedIn comment as DSM promotion:** The main post doesn't mention DSM directly — it focuses on the findings. The comment provides a soft invitation ("If you're the kind of person who likes numbered decision logs...") for those who resonate with the structure. This separates the content (blog value) from the call-to-action (DSM repo).
  - **Artifact organization:** Saving LinkedIn posts as separate files (`linkedin-post-s01.md`, `linkedin-post-s02.md`) with post text + comment text makes the workflow reproducible and keeps the blog folder organized by artifact type.
- **Scores:** Clarity 4, Applicability 4, Completeness 4, Efficiency 4 (Avg: 4.0)
- **Reasoning:** Clarity 4 — the process is now well-documented across Entry 15 and 16. Applicability 4 — worked for two different blog topics. Completeness 4 — covers research, writing, visuals, distribution, and promotion. Efficiency 4 — the second post was faster because the workflow was established.
- **Recommendation:** Add to the emerging Blog Style Guide: (1) Research step before drafting to find external data that supports claims. (2) LinkedIn comment strategy: main post = content, comment = call-to-action/links. (3) Artifact naming: `linkedin-post-{scope}.md` files include both post text and comment text.

### Entry 17: Explain Before Acting — Context for Human Validation
- **Date:** 2026-02-03 | **Sprint:** S2 Phase 2 | **Type:** Gap
- **Context:** During Phase 2 implementation, the agent began adding tests for the ablation prompt function without first explaining what was being done and why. The human reviewer rejected the change, requesting context before code.
- **Finding:** The "explain before acting" principle is critical for human-agent collaboration but isn't explicitly documented in DSM as a protocol.
  - **What happened:** Agent made the code change (test additions) immediately after completing a previous task, without pausing to explain the purpose, why these specific tests, and how they relate to the ablation study.
  - **Why it matters:** The human **wants and needs** context to evaluate whether the action is correct, necessary, and aligned with the plan. Without explanation, the human is reduced to a code reviewer rather than a collaborator.
  - **Preferred workflow:** This is the desired collaboration style: (1) Agent explains what it will do and why, (2) Human reviews and approves, (3) Agent executes. This mirrors the notebook protocol but applies to all code changes.
  - **DSM gap:** The "Notebook Collaboration Protocol" in CLAUDE.md mentions "Agent provides ONE cell at a time as a code/markdown block in conversation" but doesn't explicitly state "explain the purpose before generating the code."
- **Scores:** Clarity 2, Applicability 4, Completeness 2, Efficiency 3 (Avg: 2.75)
- **Reasoning:** Clarity 2 — the principle is implicit but not stated. Applicability 4 — the principle applies to all agent-human collaboration. Completeness 2 — neither DSM nor CLAUDE.md explicitly document this. Efficiency 3 — the rejection was quick but interrupted flow.
- **Recommendation:** (1) Add "Explain before acting" as an explicit principle in DSM 4.0 Section 2.2 (Workflow Patterns) or as a new subsection. The principle: "Before generating code, files, or making changes, the agent should explain what it will do and why, giving the human opportunity to redirect or approve." (2) Update CLAUDE.md App Development Protocol to include: "Explain **what** and **why** before creating or modifying each file — not just the file name, but the purpose and how it fits the current task."

### Entry 18: CLAUDE.md Updated — Explicit Collaboration Workflow
- **Date:** 2026-02-03 | **Sprint:** S2 Phase 2 | **Type:** Success
- **Context:** Following Entry 17's recommendation, updated `.claude/CLAUDE.md` to make the collaboration workflow explicit: (1) Agent explains what and why, (2) Human reviews and approves, (3) Agent executes.
- **Finding:** The updated CLAUDE.md now serves as a working example of how to configure human-agent collaboration for code writing projects.
  - **What was added:** "Collaboration workflow: (1) Agent explains what and why, (2) Human reviews and approves, (3) Agent executes." Plus expanded the bullet point to: "Explain **what** and **why** before creating or modifying each file — describe the purpose, the specific changes, and how they fit the current task. Wait for approval before executing."
  - **Reference for DSM:** This repo's `.claude/CLAUDE.md` can be referenced as a working example when documenting collaboration protocols in DSM 4.0. The evolution from implicit ("Explain why before...") to explicit three-step workflow demonstrates how project experience refines collaboration patterns.
  - **Bi-directional workflow:** At the end of each project, DSM should read the project's CLAUDE.md as a reference to absorb successful collaboration patterns. This closes the feedback loop: DSM informs project setup → project refines patterns → patterns feed back to DSM.
- **Scores:** Clarity 5, Applicability 5, Completeness 4, Efficiency 5 (Avg: 4.75)
- **Reasoning:** Clarity 5 — the workflow is now explicit and numbered. Applicability 5 — applies immediately to this session and future sessions. Completeness 4 — covers the core loop but could expand on edge cases (e.g., when to skip approval for trivial changes). Efficiency 5 — the fix was immediate and requires no extra steps.
- **Recommendation:** (1) Reference this repo's CLAUDE.md (`sql-query-agent-ollama/.claude/CLAUDE.md`) in DSM documentation as an example of explicit collaboration protocols. (2) Add to DSM sprint boundary checklist: "Review project's CLAUDE.md for collaboration patterns to absorb into DSM." This makes the bi-directional feedback loop explicit.

### Entry 19: Use AskUserQuestion Tool for Approval Prompts
- **Date:** 2026-02-03 | **Sprint:** S2 Phase 2 | **Type:** Gap
- **Context:** When asking "Should I proceed?" the agent used plain text instead of the `AskUserQuestion` tool, which provides clickable Yes/No buttons for the user.
- **Finding:** The collaboration workflow (explain → approve → execute) should use structured UI elements when available.
  - **What happened:** Agent wrote "Should I proceed?" as text, requiring user to type response.
  - **Better approach:** Use `AskUserQuestion` tool with Yes/No options — this shows buttons in the UI, making the approval step faster and clearer.
  - **Tool benefit:** Buttons make the approval step unambiguous. Text responses can be misinterpreted or require more typing.
- **Scores:** Clarity 3, Applicability 5, Completeness 2, Efficiency 2 (Avg: 3.0)
- **Reasoning:** Clarity 3 — the need for structured approval wasn't obvious. Applicability 5 — applies every time approval is needed. Completeness 2 — CLAUDE.md doesn't mention tool usage for approvals. Efficiency 2 — text questions slow down the workflow.
- **Recommendation:** (1) Update CLAUDE.md collaboration workflow to specify: "For approval prompts, use AskUserQuestion tool with Yes/No options instead of plain text questions." (2) Add to DSM 4.0: when the agent needs binary approval (proceed/stop), use structured prompts rather than free-text.

### Entry 20: Ablation Study — Counter-Intuitive Findings on Prompt Engineering
- **Date:** 2026-02-03 | **Sprint:** S2 Phase 2 | **Type:** Success
- **Context:** Ran EXP-002 ablation study testing 6 prompt configurations (3 prompt types × 2 schema types) across 14 queries. Total: 84 experimental runs. The study followed methodology from AbGen framework (ACL 2025) and documented research in `docs/research/ablation-study-design.md`.
- **Finding:** The ablation study produced counter-intuitive results that contradict common prompt engineering assumptions:
  - **Few-shot hurt performance:** Few-shot_full (35.7%) < Zero-shot_full (50.0%). Adding 2 examples reduced accuracy.
  - **Chain-of-thought hurt performance:** CoT_full (28.6%) was the worst configuration. Reasoning scaffold diluted SQL generation focus.
  - **Full schema better than selective:** Despite adding "noise," full schema (all 11 tables) consistently outperformed selective filtering.
  - **Best config:** Zero-shot with full schema achieved 50% EX — 7.1pp improvement over EXP-001 baseline.
  - **New limitations identified:** LIM-007 (few-shot hurts 8B models), LIM-008 (CoT hurts 8B models).
- **Why this matters for DSM:** The experiment demonstrates the value of empirical validation over literature assumptions. Research suggested few-shot and CoT would help; our data shows the opposite for llama3.1:8b on this task. This validates DSM's experiment framework (C.1.3, C.1.5) — without systematic measurement, we would have implemented the wrong prompt strategy.
- **Scores:** Clarity 5, Applicability 5, Completeness 5, Efficiency 5 (Avg: 5.0)
- **Reasoning:** Clarity 5 — ablation results are unambiguous. Applicability 5 — directly informed production configuration choice. Completeness 5 — covered all planned configurations with documented methodology. Efficiency 5 — 84 runs completed in ~15 minutes with automated runner.
- **Recommendation:** (1) Add "ablation study" as a recommended step in DSM experiment workflow when comparing prompt strategies. (2) Document the pattern: "empirical validation over literature assumptions" as a principle in DSM 4.0. (3) Reference EXP-002 as an example of productive null results — showing what doesn't work is as valuable as showing what does.

### Summary Metrics

| Metric | Value |
|--------|-------|
| Entries logged | 20 |
| Average score | 3.2 / 5 |
| Gaps found | 11 |
| Pain points | 3 |
| Successes | 6 |

### Project-Specific DSM Adaptations
1. Added Phase 0 (Research) before standard DSM_0 setup steps -- surveyed text-to-SQL state of the art to inform architecture and model selection
2. Combined PM Guidelines Templates 1 (task breakdown), 4 (prerequisites), and 7 (MUST/SHOULD/COULD) into a single sprint plan format
