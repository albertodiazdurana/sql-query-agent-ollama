# DEC-004: SQL Post-Processing for SQLite Compatibility

**Date:** 2026-02-02
**Status:** Accepted
**Sprint:** S1 Phase 2

---

## Context

During end-to-end testing (Cell 19), 2 of 3 queries failed because sqlcoder:7b generates PostgreSQL-style SQL, not SQLite:

1. **Column casing:** Model outputs `first_name`, `last_name` (snake_case). Chinook uses `FirstName`, `LastName` (PascalCase). Error: "no such column: p.first_name"
2. **ILIKE operator:** Model uses `ILIKE` for case-insensitive matching. SQLite has no `ILIKE` — it uses `LIKE` (case-insensitive by default for ASCII). Error: "near ILIKE: syntax error"
3. **NULLS LAST/FIRST:** PostgreSQL ordering syntax not supported by SQLite. Not causing errors in our tests but would in edge cases.

We first attempted to fix these via prompt engineering (Cell 20): added explicit rules like "Use LIKE not ILIKE", "Use exact column names from schema (case-sensitive)". Retesting (Cell 21) showed the model completely ignores these instructions — the exact same errors recurred. This confirms that fine-tuned models' training overrides prompt-level instructions for dialect-specific patterns.

## Decision

Add a **programmatic post-processing step** (`postprocess_sql`) applied to all LLM-generated SQL in both `generate_sql` and `handle_error`, before validation. The step performs three transformations:

1. **ILIKE → LIKE:** Regex replacement `\bILIKE\b` → `LIKE`
2. **NULLS FIRST/LAST removal:** Regex removal of `\s+NULLS\s+(FIRST|LAST)`
3. **Column name casing fix:** Build a lookup map from `schema_info` that maps both lowercase (`firstname`) and snake_case (`first_name`) variants to the actual PascalCase column names. Apply via regex identifier replacement, skipping SQL keywords.

## Rationale

- **Empirical evidence:** Prompt rules failed (Cells 20-21). Post-processing fixed both queries immediately (Cell 24), 0 retries.
- **General principle:** For fine-tuned models, training-level behaviors cannot be overridden by prompt-level instructions. Programmatic normalization is the correct pattern.
- **Research alignment:** SQL post-processing / dialect normalization is a documented technique in text-to-SQL literature.
- **Retry loop limitation:** The retry loop feeds error messages back to the model, but the model repeats the same dialect-specific patterns. Post-processing fixes the root cause; the retry loop is better suited for logic errors.

## Consequences

- The column mapping must be rebuilt if the database schema changes
- Post-processing adds a small overhead per query (negligible vs LLM latency)
- New SQLite incompatibilities from other models may require extending the post-processing rules
- The approach is generalizable: other target databases (PostgreSQL, MySQL) would need their own normalization rules
