## Sprint 1 Phase 1 + Phase 2 Checkpoint (2026-02-02)

### Scope Completion

**Phase 1: Environment & Database Setup — Complete**
- [x] Verify Ollama running and accessible from WSL (via gateway IP `172.27.64.1:11434`)
- [x] Pull models: `sqlcoder:7b` (3.8 GB), `llama3.1:8b` (4.6 GB)
- [x] Chinook SQLite database loaded (`data/chinook.db`, 11 tables)
- [x] Schema inspected and documented in notebook (Cell 3)
- [x] Row counts verified (Cell 4) — 3,503 tracks, 347 albums, 275 artists, 412 invoices
- [x] Sample rows extracted for 6 key tables (Cell 7) — for few-shot prompt embedding
- [x] Both models respond to test prompts (Cell 6)

**Phase 2: Core Agent Build — Complete**
- [x] Agent state defined: `AgentState` TypedDict with 10 fields (Cell 9)
- [x] Node 1: `schema_filter` — keyword-based table selection with FK expansion (Cell 10)
- [x] Node 2: `generate_sql` — model-aware prompt templates (Cell 13, revised from Cell 11)
- [x] Node 3: `validate_query` — sqlglot parsing + write-operation blocking (Cell 14)
- [x] Node 4: `execute_query` — SQLite execution with error capture, 20-row limit (Cell 15)
- [x] Node 5: `handle_error` — error-context retry with model-aware repair prompts (Cell 16)
- [x] LangGraph state graph wired with conditional edges (Cell 17)
- [x] SQL post-processing for SQLite compatibility (Cells 22-24): ILIKE→LIKE, NULLS LAST removal, snake_case→PascalCase column mapping (DEC-004)
- [x] Improved prompt templates with SQLite-specific rules (Cell 20)
- [x] End-to-end test: 6/6 queries pass with 0 retries (Cells 18-19, 21, 24-25)

**Completion Rate:** Phase 1: 7/7 = 100% | Phase 2: 10/10 = 100%

---

### Key Findings

1. **sqlcoder:7b requires a specific prompt format.** Generic instruction prompts (`You are a SQL expert...`) produce empty responses. The model needs `### Task / ### Database Schema / ### Answer` structure with a ` ```sql` code fence opener. This led to model-aware prompt routing in both `generate_sql` and `handle_error` nodes (see DEC-003).

2. **llama3.1:8b produces more complete SQL but is slower.** For the test query "How many albums does each artist have?": sqlcoder:7b returned `SELECT a.artistid, COUNT(*) ... GROUP BY a.artistid` (4.0s, IDs only). llama3.1:8b returned a proper JOIN with artist names (17.2s). Both are valid but llama3.1 gave a more user-friendly result.

3. **First-call latency is significantly higher.** sqlcoder:7b first call: 31.9s, subsequent: 4-5s. llama3.1:8b first call: 10.9s, subsequent: ~17s. Ollama loads models into memory on first use.

4. **Schema filtering works effectively for simple queries.** "How many albums does each artist have?" correctly selected only Album and Artist (2 of 11 tables), producing a compact 219-char schema string.

5. **sqlcoder:7b generates PostgreSQL-style SQL, not SQLite.** The model persistently uses `ILIKE`, `NULLS LAST`, and `snake_case` column names (e.g., `first_name` instead of `FirstName`). Prompt-level instructions ("Use SQLite syntax") did not override the model's training. This required a programmatic post-processing step (DEC-004).

6. **Retry loop cannot fix systematic model biases.** When the model generates `first_name` and the error says "no such column: first_name", the model retries with the same wrong casing — it doesn't learn from the error. Post-processing is the correct solution for dialect-level issues; the retry loop is best for logic errors.

7. **Genre exploration validates multi-table JOIN capability.** The agent handled a 3-table JOIN (Artist → Album → Track) with a correlated EXISTS subquery for genre filtering on the first attempt (0 retries). Result: 483 tracks across Heavy Metal/Metal/Blues, top artist Iron Maiden with 132 tracks.

---

### Quality Assessment

- **Output quality:** Good — All 6 end-to-end test queries pass with 0 retries after post-processing
- **Validation results:** All nodes pass expected cases; post-processing handles all three identified SQLite incompatibilities
- **Code quality:** Clean, modular functions with print-based tracing for notebook debugging

---

### Blockers & Issues

- **Technical blockers:** None — all resolved
- **Resolved issues:**
  - sqlcoder:7b empty-response → model-aware prompt routing (DEC-003)
  - PostgreSQL syntax in generated SQL → post-processing step (DEC-004)
  - Column name casing (snake_case vs PascalCase) → column mapping with underscore handling
- **Schema filter false positives:** Some queries select more tables than needed (e.g., 7 tables for "top 3 customers by spending"). Not harmful but adds prompt tokens. Consider improving for Phase 3.

---

### Progress Tracking

**Notebook Cells Completed:** 25 (Cells 1-25)
- Cell 1: Introduction markdown
- Cell 2: Imports & configuration
- Cell 3: Database schema inspection
- Cell 4: Row counts
- Cell 5: Ollama connectivity & model listing
- Cell 6: LLM test prompts (both models)
- Cell 7: Sample rows for few-shot prompting
- Cell 8: Phase 2 markdown header
- Cell 9: AgentState definition
- Cell 10: Node 1 — schema_filter
- Cell 11: Node 2 — generate_sql (initial, replaced by Cell 13)
- Cell 12: sqlcoder prompt format diagnosis
- Cell 13: Node 2 — generate_sql (revised, model-aware)
- Cell 14: Node 3 — validate_query
- Cell 15: Node 4 — execute_query
- Cell 16: Node 5 — handle_error
- Cell 17: LangGraph state graph wiring
- Cell 18: End-to-end test — single question (pass)
- Cell 19: End-to-end test — 3 questions (1 pass, 2 fail → identified post-processing need)
- Cell 20: Improved prompts with SQLite rules (prompt-only fix insufficient)
- Cell 21: Retest failed queries (still failing → confirmed need for post-processing)
- Cell 22: SQL post-processing function (ILIKE, NULLS LAST, column casing)
- Cell 23: Column mapping fix (snake_case → PascalCase with underscore handling)
- Cell 24: Integrated post-processing + retest (both queries pass, 0 retries)
- Cell 25: Genre exploration — Heavy Metal, Metal, Blues (both queries pass, 0 retries)

---

### End-to-End Test Results Summary

| Query | Result | Retries | Time |
|-------|--------|---------|------|
| Top 5 artists by album count | Iron Maiden (21), Led Zeppelin (14), Deep Purple (11)... | 0 | 19.1s |
| List all genres | 20 genres returned | 0 | 5.0s |
| Top 3 customers by spending | Helena Holy ($49.62), Richard Cunningham ($47.62)... | 0 | 20.8s |
| Find all tracks by AC/DC | 8 tracks (Go Down, Dog Eat Dog, Let There Be Rock...) | 0 | 8.1s |
| Track count for Heavy Metal/Metal/Blues | 483 tracks | 0 | 18.0s |
| Top 5 artists in Metal/Blues genres | Iron Maiden (132), Metallica (112), Eric Clapton (32)... | 0 | 27.0s |

**All 6 queries: 0 retries, 100% success rate with post-processing**

---

### Decision Log Updates

- **DEC-003:** Model-aware prompt templates
  - Context: sqlcoder:7b returned empty SQL with generic prompts
  - Decision: Route to model-specific prompt formats based on model name
  - Impact: Both generate_sql and handle_error use template routing

- **DEC-004:** SQL post-processing for SQLite compatibility
  - Context: sqlcoder:7b generates PostgreSQL-style SQL; prompt rules don't override training
  - Decision: Add programmatic post-processing (ILIKE→LIKE, NULLS LAST removal, column casing)
  - Impact: Fixes dialect-level issues without relying on retry loop

---

### Phase 2 Success Criteria — Met

| Criterion | Target | Result |
|-----------|--------|--------|
| Agent completes 3+ simple queries end-to-end | 3+ queries | 6/6 queries pass |
| Retry loop triggers and recovers from at least 1 error | 1 recovery | Tested in Cell 16 (handle_error repairs bad SQL) |
| sqlglot validation catches syntax errors before execution | Catches errors | Confirmed in Cell 14 |
| Destructive queries are blocked | Blocked | DROP blocked in Cell 14 |

---

### Next Steps

1. Phase 3: Design evaluation test suite (Easy/Medium/Hard queries)
2. Implement metrics collection (EX, Parsability, Retry Rate, Latency, Error Categories)
3. Run full comparison: sqlcoder:7b vs llama3.1:8b on same test suite
4. Document findings and select best model for Sprint 2

---

### Notes & Learnings

- **What worked well:** Building and testing each node individually before wiring the graph. Caught the sqlcoder prompt issue early (Cell 12) rather than debugging it inside a full graph. The iterative approach to fixing failures (prompt rules → post-processing) documented the discovery process clearly.
- **What could be improved:** Could have checked sqlcoder's expected prompt format before writing the first generate_sql (Cell 11). Could have anticipated the PostgreSQL dialect issue given sqlcoder's training data.
- **Key insight:** For fine-tuned models, prompt-level instructions cannot override training-level behaviors. Programmatic post-processing is the correct pattern for dialect normalization — this is a general principle applicable to any code-generation model.

---

**Checkpoint completed by:** Alberto
**Next checkpoint:** After Sprint 1 Phase 3 completion (evaluation framework + model comparison)
