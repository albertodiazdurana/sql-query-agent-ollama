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

**Phase 2: Core Agent Build — Nodes Complete, Graph Wiring Pending**
- [x] Agent state defined: `AgentState` TypedDict with 10 fields (Cell 9)
- [x] Node 1: `schema_filter` — keyword-based table selection with FK expansion (Cell 10)
- [x] Node 2: `generate_sql` — model-aware prompt templates (Cell 13, revised from Cell 11)
- [x] Node 3: `validate_query` — sqlglot parsing + write-operation blocking (Cell 14)
- [x] Node 4: `execute_query` — SQLite execution with error capture, 20-row limit (Cell 15)
- [x] Node 5: `handle_error` — error-context retry with model-aware repair prompts (Cell 16)
- [ ] LangGraph state graph wiring with conditional edges (Cell 17 — next)
- [ ] End-to-end test with multiple questions

**Completion Rate:** Phase 1: 7/7 = 100% | Phase 2: 6/8 = 75%

---

### Key Findings

1. **sqlcoder:7b requires a specific prompt format.** Generic instruction prompts (`You are a SQL expert...`) produce empty responses. The model needs `### Task / ### Database Schema / ### Answer` structure with a ````sql` code fence opener. This led to model-aware prompt routing in both `generate_sql` and `handle_error` nodes (see DEC-003).

2. **llama3.1:8b produces more complete SQL but is slower.** For the test query "How many albums does each artist have?": sqlcoder:7b returned `SELECT a.artistid, COUNT(*) ... GROUP BY a.artistid` (4.0s, IDs only). llama3.1:8b returned a proper JOIN with artist names (17.2s). Both are valid but llama3.1 gave a more user-friendly result.

3. **First-call latency is significantly higher.** sqlcoder:7b first call: 31.9s, subsequent: 4-5s. llama3.1:8b first call: 10.9s, subsequent: ~17s. Ollama loads models into memory on first use.

4. **Schema filtering works effectively for simple queries.** "How many albums does each artist have?" correctly selected only Album and Artist (2 of 11 tables), producing a compact 219-char schema string.

5. **sqlglot catches syntax errors and sqlcoder repair works.** Deliberate bad SQL (`SELECT Foo FROM Artist`) was caught by sqlglot, and the error repair node produced valid corrected SQL. Repair latency was high (62s) but functional.

---

### Quality Assessment

- **Output quality:** Good — All 5 nodes individually tested with correct behavior
- **Validation results:** All nodes pass expected cases (valid input, error input, edge cases)
- **Code quality:** Clean, modular functions with print-based tracing for notebook debugging

---

### Blockers & Issues

- **Technical blockers:** None
- **Data/resource issues:** sqlcoder:7b repair latency is high (~62s for error correction). May need to investigate if this is model loading or prompt complexity.
- **Conceptual challenges:** sqlcoder:7b empty-response issue required prompt format investigation (Cell 12). Resolved by adopting model-specific prompt templates.
- **Mitigation actions taken:** Created model-aware prompt routing (DEC-003)

---

### Progress Tracking

**Notebook Cells Completed:** 16 (Cells 1-16)
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

---

### Decision Log Updates

- **DEC-003:** Model-aware prompt templates
  - Context: sqlcoder:7b returned empty SQL with generic prompts
  - Decision: Route to model-specific prompt formats based on model name
  - Impact: Both generate_sql and handle_error use template routing

---

### Next Steps

1. Wire LangGraph state graph with conditional edges (Cell 17)
2. End-to-end test: run full agent on 3+ questions
3. Phase 3: Design evaluation test suite and metrics framework
4. Compare sqlcoder:7b vs llama3.1:8b systematically

**Success Criteria for Phase 2 Completion:**
- Agent completes 3+ simple queries end-to-end
- Retry loop triggers and recovers from at least 1 error

---

### Notes & Learnings

- **What worked well:** Building and testing each node individually before wiring the graph. Caught the sqlcoder prompt issue early (Cell 12) rather than debugging it inside a full graph.
- **What could be improved:** Could have checked sqlcoder's expected prompt format before writing the first generate_sql (Cell 11), avoiding the need for a revision.
- **Insights for next steps:** The latency difference between models suggests we should track latency as a first-class evaluation metric alongside accuracy.

---

**Checkpoint completed by:** Alberto
**Next checkpoint:** After Sprint 1 Phase 2 completion (graph wired + end-to-end tests pass)
