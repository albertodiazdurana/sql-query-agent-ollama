# DEC-005: Default Model Selection — llama3.1:8b for Sprint 2

**Date:** 2026-02-02
**Status:** Accepted
**Sprint:** S1 Phase 3 (Sprint Boundary)

---

## Context

EXP-001 (Text-to-SQL Model Comparison) evaluated `sqlcoder:7b` and `llama3.1:8b` on a 14-query test suite (5 Easy, 5 Medium, 4 Hard) against the Chinook SQLite database. The experiment was designed to select the default model for the Sprint 2 Streamlit application.

**Headline result:** Both models achieved identical Execution Accuracy — 6/14 (42.9%). The decision must be based on secondary metrics and qualitative differences.

## Decision

Use **llama3.1:8b** as the default model for Sprint 2, with `sqlcoder:7b` available as an alternative.

## Rationale

Despite equal EX scores, the models have fundamentally different failure profiles:

| Metric | sqlcoder:7b | llama3.1:8b | Winner |
|--------|-------------|-------------|--------|
| Execution Accuracy | 42.9% (6/14) | 42.9% (6/14) | Tie |
| Raw Parsability | 85.7% (12/14) | **100%** (14/14) | llama3.1 |
| Effective Parsability | 64.3% (9/14) | **92.9%** (13/14) | llama3.1 |
| Avg Latency | 30.3s | **17.6s** | llama3.1 |
| Easy Queries | 80% (4/5) | **100%** (5/5) | llama3.1 |
| Table Hallucination | 2 instances (`payment`, `invoiceintrack`) | **0 instances** | llama3.1 |
| Retry Rate | 21.4% (3/14) | **14.3%** (2/14) | llama3.1 |

**Key differentiators:**

1. **Zero hallucination:** llama3.1:8b never invented non-existent tables. sqlcoder:7b hallucinated `payment` (M2) and `invoiceintrack` (H4) — tables that don't exist in the Chinook schema. This is a critical reliability concern for a user-facing application.

2. **100% parsability:** llama3.1:8b always produced syntactically valid SQL. sqlcoder:7b produced unparseable output on 2 hard queries (H2, H3), likely due to context overflow.

3. **1.7x faster:** 17.6s vs 30.3s average latency. For an interactive application, lower latency improves user experience significantly.

4. **Perfect Easy accuracy:** llama3.1:8b scored 100% on Easy queries (the most common use case for a NL-to-SQL tool), while sqlcoder:7b missed one (E3, a LIMIT 1 query that returned all max-price tracks).

5. **Simpler prompting:** llama3.1:8b works with generic instruction prompts. sqlcoder:7b requires a specific `### Task / ### Database Schema / ### Answer` format (DEC-003), adding complexity.

**Why not sqlcoder:7b?** Despite being fine-tuned specifically for SQL, sqlcoder:7b's advantages (slightly better Medium accuracy: 2/5 vs 1/5) are outweighed by its risks: hallucinated tables that waste retry cycles, runtime failures on complex queries, slower latency, and prompt format dependencies.

## Consequences

- Sprint 2 Streamlit app will default to `llama3.1:8b`
- `sqlcoder:7b` remains available as an option (useful for users who want SQL-specific tuning)
- Model-aware prompting (DEC-003) and SQL post-processing (DEC-004) remain active — they are needed regardless of model choice
- The 42.9% overall EX means Sprint 2 should focus on improving accuracy (better schema filtering, few-shot examples, prompt engineering) rather than just shipping the current agent
- Medium and Hard query accuracy (both models: 20% and 0% respectively) is the primary area for improvement
