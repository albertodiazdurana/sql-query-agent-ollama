# DEC-002: Consolidate Feedback Files Under docs/feedback/

**Date:** 2026-02-01
**Status:** Accepted
**Sprint:** S1 Setup

---

## Context

DSM places the Validation Tracker at the `docs/` root and feedback files (backlogs, methodology, blog) also at the `docs/` level. This scatters related artifacts across the directory, making them harder to find and maintain together.

## Decision

Group **all DSM feedback artifacts** under a single `docs/feedback/` folder:
- `backlogs.md` -- DSM improvement proposals
- `methodology.md` -- project methodology record (now includes section scoring)
- `blog.md` -- blog materials tracker

## Rationale

- **Single location:** All feedback-related files are co-located and easy to find
- **Clarity:** Reduces clutter at the `docs/` root level
- **Consistency:** Mirrors the pattern of other `docs/` subdirectories (`plans/`, `decisions/`, `checkpoints/`, `research/`)

## Consequences

- Paths differ from DSM default layout -- documented in CLAUDE.md project structure
- The Validation Tracker has been merged into `methodology.md` per DSM v1.3.19 (BACKLOG-041), so only 3 files remain in this folder
