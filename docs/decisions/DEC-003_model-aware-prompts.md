# DEC-003: Model-Aware Prompt Templates

**Date:** 2026-02-02
**Status:** Accepted
**Sprint:** S1 Phase 2

---

## Context

During the Core Agent Build phase, the `generate_sql` node was initially implemented with a single generic instruction prompt (`You are a SQL expert...`). When tested with `sqlcoder:7b`, the model returned an empty string — no SQL was generated. The same prompt worked correctly with `llama3.1:8b`.

Investigation (Cell 12) revealed that `sqlcoder:7b` is fine-tuned on a specific prompt format using markdown headers (`### Task`, `### Database Schema`, `### Answer`) and expects a SQL code fence opener to begin generation. Generic instruction prompts fall outside its training distribution.

## Decision

Implement **model-aware prompt routing** in both the `generate_sql` and `handle_error` nodes. The model name is checked at runtime to select the appropriate prompt template:

- **sqlcoder models** → `### Task / ### Database Schema / ### Answer` format with ````sql` opener
- **All other models** → Generic instruction format (`You are a SQL expert...`)

## Rationale

- **Empirical evidence:** Side-by-side test (Cell 12) showed generic prompt → empty response, sqlcoder-style prompt → correct SQL in 5.5s
- **Model-specific tuning:** Fine-tuned models often require their training prompt format to perform well. This is well-documented for code-generation models.
- **Extensibility:** The routing pattern (`if "sqlcoder" in model`) is simple to extend for future models (e.g., `duckdb-nsql`, `starcoder`)
- **Affects two nodes:** Both SQL generation and error repair need model-appropriate prompts, so the pattern is applied consistently

## Consequences

- Two prompt templates must be maintained per function (generation + repair = 4 templates total)
- New models may require adding a new template and routing condition
- The model name string becomes a functional input, not just a label — must match expected patterns
