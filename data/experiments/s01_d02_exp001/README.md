# EXP-001: Text-to-SQL Model Comparison

**Sprint:** 1 | **Day:** 2 | **Date:** 2026-02-02
**DSM Reference:** C.1.3 (Capability Experiment Template), C.1.5 (Limitation Discovery), 5.2.1 (Experiment Tracking)
**Related Decisions:** DEC-003 (model-aware prompts), DEC-004 (SQL post-processing)

---

## Summary

Compare `sqlcoder:7b` (SQL-specialized fine-tune) against `llama3.1:8b` (general-purpose baseline) on a curated test suite of 14 natural language to SQL queries across three difficulty levels. Both models run through the same LangGraph agent pipeline with SQL post-processing for SQLite dialect normalization.

---

## Experiment Design (C.1.3 Required Fields)

| Field | Value |
|-------|-------|
| **experiment_id** | EXP-001 |
| **experiment_name** | Text-to-SQL Model Comparison: sqlcoder:7b vs llama3.1:8b |
| **objective** | Determine which model produces more accurate SQL across varying query difficulties |
| **evaluation_type** | Both (Quantitative metrics + Qualitative observations) |

### Hypothesis

1. **H1 (Accuracy):** sqlcoder:7b will achieve higher Execution Accuracy than llama3.1:8b due to SQL-specific fine-tuning (research finding: SQL fine-tunes outperform general-purpose by 15-20% on Spider EX)
2. **H2 (Readability):** llama3.1:8b will produce more readable SQL (JOINs for human-friendly output, column names in results) but at higher latency
3. **H3 (Post-processing):** sqlcoder:7b will require post-processing more frequently due to PostgreSQL dialect bias (confirmed in Phase 2: ILIKE, NULLS LAST, snake_case columns)

### Rejection Criteria (defined BEFORE testing)

- H1 rejected if: llama3.1:8b EX >= sqlcoder:7b EX
- H2 rejected if: sqlcoder:7b produces JOINs with names at same rate as llama3.1:8b
- H3 rejected if: sqlcoder:7b post-processing rate <= llama3.1:8b post-processing rate

---

## Test Setup

### Configuration

| Parameter | Value |
|-----------|-------|
| **Models** | `sqlcoder:7b`, `llama3.1:8b` |
| **Temperature** | 0 (deterministic) |
| **num_ctx** | 8192 |
| **Database** | Chinook SQLite (11 tables, 3,503 tracks) |
| **Agent** | LangGraph 5-node graph (Phase 2) with post-processing |
| **Max retries** | 3 |
| **Prompt templates** | Model-aware (DEC-003): sqlcoder format vs generic format |
| **Post-processing** | Active (DEC-004): ILIKE→LIKE, NULLS LAST removal, column casing |
| **Ollama host** | `172.27.64.1:11434` (Windows host via WSL gateway) |

### Metrics Tracked

**Quantitative (per sprint plan + Phase 2 adjustments):**

| Metric | Description | Threshold | Source |
|--------|-------------|-----------|--------|
| Execution Accuracy (EX) | Query returns correct results | >= 60% | Sprint plan (primary) |
| Raw Parsability | Valid SQL before post-processing | Informational | Plan adjustment |
| Effective Parsability | Valid SQL after post-processing, first attempt | >= 70% | Sprint plan |
| Retry Rate | % of queries needing error correction | Informational | Sprint plan |
| Post-Processing Rate | % of queries needing dialect normalization | Informational | Plan adjustment |
| Avg Latency | Seconds from question to answer | Informational | Sprint plan |

**Qualitative (error categorization):**

| Error Category | Definition |
|----------------|------------|
| Schema linking | Wrong table or column selected |
| Syntax | Invalid SQL that fails parsing |
| Dialect | PostgreSQL syntax in SQLite context (ILIKE, NULLS LAST, snake_case) |
| Logic | Valid SQL, executes, but wrong results |
| Hallucination | References non-existent tables, columns, or values |

---

## Test Suite

14 fresh queries (not reusing Phase 2 ad-hoc queries), organized by difficulty per sprint plan.

### Easy (5 queries) — Single table, simple WHERE, basic aggregation

| ID | Question | Expected Result | Tables Needed |
|----|----------|-----------------|---------------|
| E1 | How many employees are there? | 8 | Employee |
| E2 | List all media types | 5 types (MPEG, AAC, etc.) | MediaType |
| E3 | What is the most expensive track? | Track with max UnitPrice | Track |
| E4 | How many customers are from Brazil? | Count of Brazilian customers | Customer |
| E5 | Show the 5 longest tracks by duration | Top 5 by Milliseconds, desc | Track |

### Medium (5 queries) — JOINs, GROUP BY + HAVING, ORDER BY + LIMIT

| ID | Question | Expected Result | Tables Needed |
|----|----------|-----------------|---------------|
| M1 | Which genre has the most tracks? | Rock (1,297 tracks) | Track, Genre |
| M2 | How much has each customer spent in total? Show top 5. | Top 5 by SUM(Invoice.Total) | Customer, Invoice |
| M3 | List albums that have more than 20 tracks | Albums with COUNT(Track) > 20 | Album, Track |
| M4 | Which employees support the most customers? | Employees by COUNT(Customer) | Employee, Customer |
| M5 | What are the top 3 best-selling genres by revenue? | Genres by SUM(InvoiceLine.UnitPrice * Quantity) | Genre, Track, InvoiceLine |

### Hard (4 queries) — Multi-table JOINs, subqueries, complex aggregation, string matching

| ID | Question | Expected Result | Tables Needed |
|----|----------|-----------------|---------------|
| H1 | Which artists have tracks in more than 2 genres? | Artists with genre count > 2 | Artist, Album, Track, Genre |
| H2 | Find customers who have never purchased a Jazz track | Customers NOT IN Jazz purchases | Customer, Invoice, InvoiceLine, Track, Genre |
| H3 | What is the average invoice total by country, only for countries with more than 5 customers? | AVG(Total) with HAVING COUNT(Customer) > 5 | Customer, Invoice |
| H4 | List the top 3 playlists by total track duration in hours | Playlists by SUM(Milliseconds) / 3600000 | Playlist, PlaylistTrack, Track |

---

## Quantitative Results

### Per-Model Summary

| Metric | sqlcoder:7b | llama3.1:8b | Delta |
|--------|-------------|-------------|-------|
| Execution Accuracy (EX) | 6/14 (42.9%) | 6/14 (42.9%) | 0 |
| Raw Parsability | 12/14 (85.7%) | 14/14 (100%) | +2 |
| Effective Parsability | 9/14 (64.3%) | 13/14 (92.9%) | +4 |
| Retry Rate | 3/14 (21.4%) | 2/14 (14.3%) | -1 |
| Post-Processing Rate | 1/14 (7.1%)* | 2/14 (14.3%)* | +1 |
| Avg Latency (s) | 30.3s | 17.6s | -12.7s |

*Post-Processing Rate is unreliable — see LIM-003 and ED-1 risk note.

### Per-Difficulty Breakdown

| Difficulty | sqlcoder:7b EX | llama3.1:8b EX | sqlcoder:7b Latency | llama3.1:8b Latency |
|------------|----------------|----------------|---------------------|---------------------|
| Easy (5) | 4/5 (80%) | 5/5 (100%) | 9.1s | 6.8s |
| Medium (5) | 2/5 (40%) | 1/5 (20%) | 39.5s | 13.5s |
| Hard (4) | 0/4 (0%) | 0/4 (0%) | 45.4s | 36.2s |

### Per-Query Results

| ID | Difficulty | sqlcoder:7b | llama3.1:8b | sqlcoder err | llama err |
|----|-----------|-------------|-------------|--------------|-----------|
| E1 | Easy | PASS | PASS | | |
| E2 | Easy | PASS | PASS | | |
| E3 | Easy | FAIL | PASS | logic | |
| E4 | Easy | PASS | PASS | | |
| E5 | Easy | PASS | PASS | | |
| M1 | Medium | PASS | PASS | | |
| M2 | Medium | FAIL | FAIL | hallucination | logic |
| M3 | Medium | FAIL | FAIL | logic | logic |
| M4 | Medium | PASS | FAIL | | logic |
| M5 | Medium | FAIL | FAIL | dialect | logic |
| H1 | Hard | FAIL | FAIL | logic | schema_linking |
| H2 | Hard | FAIL | FAIL | runtime | logic |
| H3 | Hard | FAIL | FAIL | runtime | logic |
| H4 | Hard | FAIL | FAIL | hallucination | logic |

---

## Qualitative Results

### Error Category Distribution

| Category | sqlcoder:7b | llama3.1:8b |
|----------|-------------|-------------|
| logic | 3 | 7 |
| hallucination | 2 | 0 |
| runtime | 2 | 0 |
| dialect | 1 | 0 |
| schema_linking | 0 | 1 |
| **Total failures** | **8** | **8** |

### Error Pattern Analysis

| Query ID | Model | Error Category | Issue | Notes |
|----------|-------|----------------|-------|-------|
| E3 | sqlcoder | logic | Included Composer column — extra column changed tuple comparison | llama returned exact 2-column match |
| M2 | sqlcoder | hallucination | Invented `payment` table (3 retries, never self-corrected) | Correct table is Invoice |
| M2 | llama | logic | Returned wrong column structure | Valid SQL but wrong result format |
| M3 | both | logic | Row count mismatch vs ground truth | Both generated valid SQL, different result sets |
| M4 | llama | logic | Included EmployeeId in SELECT — extra column changed comparison | sqlcoder returned exact 3-column match |
| M5 | sqlcoder | dialect | Used `media_type` (snake_case) — post-processing fixed column names but not table names | Correct table: MediaType |
| M5 | llama | logic | Used `T.UnitPrice * T.Bytes` instead of InvoiceLine | Did not join InvoiceLine table |
| H1 | sqlcoder | logic | Correct query structure but row count/content mismatch | Returned 11 artists; GT has 7 (ordering diff?) |
| H1 | llama | schema_linking | `T.ArtistId` — Track has no ArtistId column (goes through Album) | 3 retries, same error each time |
| H2 | sqlcoder | runtime | LLM output exceeded context or produced unparseable text | Complex subquery may exceed 8192 context |
| H2 | llama | logic | Compared CustomerId to TrackId in subquery | Incorrect NOT IN subquery join |
| H3 | sqlcoder | runtime | LLM output exceeded context or produced unparseable text | Complex aggregation query |
| H3 | llama | logic | Used BillingCountry from Invoice instead of joining Customer for HAVING | Counted invoices, not customers |
| H4 | sqlcoder | hallucination | Invented `invoiceintrack` table (3 retries) | Correct table: PlaylistTrack |
| H4 | llama | logic | Used `Milliseconds / 3600.0` instead of `/ 3600000.0` | Wrong unit conversion |

### Capability Observations

| Observation | sqlcoder:7b | llama3.1:8b |
|-------------|-------------|-------------|
| Uses JOINs for readable output | Yes, but less consistent aliasing | Yes, consistent table aliases (A, T, G) |
| Handles multi-table queries | Fails on 3+ tables (hallucinated tables) | Fails on 3+ tables (wrong join paths) |
| Correct GROUP BY / HAVING | Yes for simple cases (M1) | Yes for simple cases (M1) |
| String matching (LIKE) | Not tested in EXP-001 | Not tested in EXP-001 |
| Subquery generation | Failed (H2 runtime, H3 runtime) | Attempted but logically incorrect (H2) |

---

## Findings

### Hypothesis Evaluation

| Hypothesis | Result | Evidence |
|-----------|--------|----------|
| H1: sqlcoder EX > llama EX | **REJECTED** | Both 6/14 (42.9%). SQL fine-tuning provides no EX advantage at 7-8B scale on this test suite. Research predicted 15-20% advantage — not observed. |
| H2: llama produces more readable SQL | **PARTIALLY CONFIRMED** | llama uses consistent table aliases and JOINs. sqlcoder also uses JOINs but with less consistent aliasing. Qualitative assessment — no automated metric. |
| H3: sqlcoder needs more post-processing | **INCONCLUSIVE** | ED-1 risk materialized: post-processing is inside generate_sql, so raw_sql ≈ final_sql. PP metric unreliable (LIM-003). Phase 2 observations confirm sqlcoder produces more PostgreSQL-isms, but cannot quantify from EXP-001 data. |

### Quantitative Summary
- **Execution Accuracy:** 6/14 vs 6/14 — both below the 60% sprint target (42.9%)
- **Parsability:** llama 100% raw / 92.9% effective vs sqlcoder 85.7% / 64.3% — llama significantly more reliable
- **Efficiency:** llama 1.7x faster overall (17.6s vs 30.3s), 2.9x faster on Medium queries
- **Post-Processing:** Not reliably separable (LIM-003). Sprint 2 needs architectural fix.

### Confirmed Capabilities
- Both models solve single-table Easy queries reliably (80-100% EX)
- Both generate syntactically valid SQL for simple schemas
- llama3.1:8b produces 100% parsable output (never crashes)
- Retry loop works for recoverable errors but not for systematic biases (LIM-004)
- Post-processing successfully handles ILIKE→LIKE and column casing (Phase 2 evidence)

### Limitations Identified
- LIM-001: Hard queries (0% EX both models) — 7-8B model capability ceiling
- LIM-002: sqlcoder hallucinated 3 non-existent tables — model-specific defect
- LIM-003: Post-processing metrics not separable — measurement architecture issue
- LIM-004: Retry loop reproduces same errors at temperature=0
- LIM-005: EX metric false positive risk on row-count comparison
- LIM-006: Keyword-based schema filter over-selects tables, adding noise

### Edge Cases
- **E3 divergence:** sqlcoder included an extra column (Composer) which changed the tuple comparison. The SQL was semantically correct but failed EX due to format mismatch. This highlights ED-2's limitation: column selection affects comparison even when the answer is right.
- **M4 divergence:** llama included EmployeeId in output, changing the tuple structure. Same issue — correct answer, wrong format for comparison.
- **H2/H3 sqlcoder runtime:** These queries produced unparseable output, suggesting context window exhaustion on complex multi-table queries with 8192 num_ctx.
- **H4 unit conversion:** llama divided by 3600.0 instead of 3600000.0 (milliseconds to hours). Close to correct logic but off by 1000x — a common unit conversion error.

### Model Recommendation for Sprint 2

**Default model: llama3.1:8b**

| Factor | llama3.1:8b | sqlcoder:7b |
|--------|-------------|-------------|
| Accuracy | 42.9% EX | 42.9% EX |
| Reliability | 100% parsable, no crashes | 85.7% parsable, 2 runtime failures |
| Speed | 17.6s avg | 30.3s avg |
| Hallucination | None observed | 3 hallucinated tables |
| Retry cost | 14.3% retry rate | 21.4% retry rate |

sqlcoder:7b should remain available as an alternative but not as default. Its hallucination of non-existent tables is a usability risk for a user-facing application.

**Sprint 2 improvement priorities:**
1. Separate post-processing into its own graph node (fixes LIM-003)
2. Add schema-aware validation: reject SQL referencing non-existent tables/columns (mitigates LIM-002, LIM-004)
3. Improve schema filtering: embedding-based or LLM-based (addresses LIM-006)
4. Test larger models if VRAM allows (addresses LIM-001)
5. Add few-shot examples per difficulty level

---

## Limitation Tracking (C.1.5)

| ID | Description | Type | Severity | Disposition | Tracking |
|----|-------------|------|----------|-------------|----------|
| LIM-001 | 7-8B models cannot solve multi-table Hard queries (0/4 both models) | Capability ceiling | High | Accept for MVP; test larger models | Sprint 2 backlog |
| LIM-002 | sqlcoder:7b hallucinates table names from training data (payment, media_type, invoiceintrack) | Model-specific defect | High | Mitigated by llama default; add schema validation | DEC-005, Sprint 2 |
| LIM-003 | Post-processing metrics unreliable — PP inside generate_sql, not separable by streaming | Measurement limitation | Medium | Refactor PP into separate graph node | Sprint 2 architecture |
| LIM-004 | Retry loop cannot fix systematic model biases at temperature=0 | Architecture limitation | Medium | Schema-aware validation; temperature diversity on retries | Sprint 2 error handling |
| LIM-005 | EX metric false positive risk on row-count comparison (ED-2 known limitation) | Measurement limitation | Low | Accept for Sprint 1; full result-set comparison in Sprint 2 | Sprint 2 eval |
| LIM-006 | Keyword-based schema filter over-selects tables, adds noise to prompts | Architecture limitation | Medium | Evaluate embedding-based or LLM-based filtering | Sprint 2 schema_filter |

---

## Evaluation Harness Design Decisions (Cell 28)

Decisions made during the evaluation harness implementation, documented for traceability.

### ED-1: Raw SQL capture via `graph.stream()`

**Decision:** Use LangGraph's `graph.stream()` to capture the SQL output from the `generate_sql` node before post-processing, rather than modifying `AgentState` or calling the LLM twice.

**Rationale:** Three options were considered:
1. ~~Modify AgentState to add `raw_sql` field~~ — Requires redefining earlier cells (9, 17), breaking notebook linearity
2. ~~Call LLM twice (once for raw SQL, once via graph)~~ — Doubles latency per query (est. +5-20s each), 28 extra LLM calls total
3. **Use `graph.stream()`** — Yields state updates per node, captures `generated_sql` from `generate_sql` node before subsequent nodes modify it. Zero overhead, no code changes to existing cells.

**Risk:** If post-processing is integrated *inside* `generate_sql` (rather than as a separate node), `raw_sql` will already be post-processed and `raw_sql == final_sql`. In that case, Raw Parsability and Post-Processing Rate metrics will be reported as "not separable." We accept this risk and will note it in results.

### ED-2: Execution Accuracy comparison strategy

**Decision:** Use a flexible comparison function with three modes based on ground truth type:
- **Scalar GT** (int/float): If agent returns `[(N,)]` (1 row, 1 col), compare value. If agent returns multiple rows, compare row count.
- **Tuple GT** (single row): Compare first row values element-wise.
- **List GT** (multi-row): Compare row count AND first row values.

**Rationale:** The standard Spider benchmark EX metric runs both gold and predicted SQL and compares result sets. Our adaptation is needed because:
1. Ground truth is pre-computed (not re-executed), so formats vary (scalar from `.scalar()`, tuple from `.fetchone()`, list from `.fetchall()`)
2. The agent may return data in a different format than the gold SQL (e.g., `SELECT COUNT(*)` vs `SELECT *` for "How many..." questions)
3. The dual check for scalar GT (value match OR row count match) handles both count queries (E1: "How many employees?" → agent returns `[(8,)]`) and list queries (E2: "List all media types" → agent returns 5 rows)

**Known limitation:** Row count comparison can produce false positives if the agent returns the right number of rows but wrong content. This is a known limitation of EX-based evaluation (also present in Spider). We mitigate by also checking first-row values for list GT.

**Float tolerance:** 0.01 for aggregation results (SUM, AVG) to handle floating-point arithmetic differences.

### ED-3: Error categorization hierarchy

**Decision:** Assign error categories in priority order: schema_linking → syntax → dialect → hallucination → logic → unknown.

**Rationale:** Categories are checked from most specific to most general:
1. **schema_linking** first: "no such column" / "ambiguous" in error text — these are unambiguous signals
2. **syntax**: raw SQL fails sqlglot parsing — detected before execution
3. **dialect**: post-processing was applied but query still failed — indicates dialect issues beyond what post-processing handles
4. **hallucination**: "no such table" in error — references non-existent schema elements
5. **logic**: query executed successfully but returned wrong results — catch-all for semantic errors
6. **unknown**: none of the above matched

This is a single-label classification (each failure gets one category). When multiple categories could apply, the earlier check wins. This prioritizes actionable categories (schema linking is fixable via better schema filtering) over vague ones (logic errors require deeper analysis).

---

## Files

| File | Description |
|------|-------------|
| `README.md` | This document — experiment design, results, and findings |
| `run_experiment.py` | EXP-001 runner script — reconstructs agent, runs evaluation, saves JSON |
| `results_sqlcoder_7b.json` | sqlcoder:7b per-query results (14 queries) |
| `results_llama3_1_8b.json` | llama3.1:8b per-query results (14 queries) |
| `../../scripts/eval_harness.py` | Reusable evaluation framework (EvalResult, comparison, categorization) |
| Notebook Cells 27, 29-32 | Test suite definition (27), results loading and analysis (29-32) |

---

## References & Citations

### DSM Framework
- DSM C.1.3: Capability Experiment Template — structure for this experiment
- DSM C.1.5: Limitation Discovery Protocol — LIM-### format for findings
- DSM C.1.6: Experiment Artifact Organization — folder structure and registry
- DSM 5.2.1: Experiment Tracking — parameter and metric logging requirements
- DSM 4.0 §4.4: Tests vs Capability Experiments — classification of this evaluation as an experiment

### Project Decisions
- DEC-003: Model-aware prompt templates — sqlcoder:7b requires `### Task` format
- DEC-004: SQL post-processing for SQLite compatibility — ILIKE→LIKE, NULLS LAST, column casing

### External References
- **Spider benchmark (Execution Accuracy):** Yu et al., "Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task" (EMNLP 2018). EX metric: predicted SQL is correct if its execution result matches the gold SQL's execution result. Our `compare_results` function adapts this approach with pre-computed ground truth. Reference: `docs/research/text_to_sql_state_of_art.md`
- **LangGraph streaming API:** `graph.stream()` yields `{node_name: state_update}` dicts per node execution. Used in ED-1 to capture intermediate state without modifying the graph. Reference: LangGraph documentation, `langgraph` package
- **sqlglot parsing:** Used in `check_sql_parsable()` for raw parsability metric — same validation library used in the agent's `validate_query` node (Cell 14). Reference: `sqlglot` package

### Project Research
- `docs/research/text_to_sql_state_of_art.md` — benchmarks, approaches, model comparisons that informed test suite design and metric selection
