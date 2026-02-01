# DEC-001: Use Chinook Database as Sample

**Date:** 2026-02-01
**Status:** Accepted
**Sprint:** S1 Setup

---

## Context

The project needs a sample SQL database for development, testing, and evaluation of the text-to-SQL agent. The database must have a realistic schema with enough complexity to exercise schema filtering, multi-table joins, and aggregation queries.

## Decision

Use the **Chinook database** as the primary sample database.

## Rationale

- **Well-known schema:** 11 tables covering music, invoices, customers, and employees
- **Widely used in SQL tutorials:** Makes it easy to find reference queries and expected results
- **Benchmarking:** Enables comparison with other text-to-SQL projects that use the same schema
- **Appropriate complexity:** Multiple relationships (1:N, M:N via junction tables) without being overwhelming for 7B models
- **Readily available:** SQLite version freely downloadable

## Consequences

- Evaluation results are comparable to other projects using Chinook
- The schema is well-documented, reducing ambiguity in query evaluation
- If additional complexity is needed later, a second database can be added alongside Chinook
