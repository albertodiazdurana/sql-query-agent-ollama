# Sprint 2 Phase 2 Checkpoint — Ablation Study Complete (2026-02-03)

## Session Overview

| Item | Planned | Actual |
|------|---------|--------|
| **Sprint** | Sprint 2: Streamlit Application | In progress |
| **Phase** | Phase 2: Agent Improvements (Ablation Study) | COMPLETE |
| **Configurations tested** | 6 (3 prompts × 2 schema types) | 6 |
| **Total runs** | 84 (6 configs × 14 questions) | 84 |
| **Best EX** | Improve on 42.9% baseline | 50% (zero_shot_full) |
| **DSM feedback entries** | Entry 20 | Added |

---

## What Was Done This Session

### EXP-002 Ablation Study

**Objective:** Measure impact of prompt engineering choices on text-to-SQL accuracy

**Variables tested:**
1. Prompt structure: Zero-shot, Few-shot (2 examples), Chain-of-thought
2. Schema context: Full (all 11 tables), Selective (question-relevant only)

**Results:**

| Configuration | EX | VV | Latency |
|--------------|-----|-----|---------|
| **zero_shot_full** | **7/14 (50%)** | 14/14 | 8.97s |
| zero_shot_selective | 6/14 (43%) | 13/14 | 12.17s |
| few_shot_full | 5/14 (36%) | 14/14 | 8.46s |
| few_shot_selective | 6/14 (43%) | 14/14 | 11.54s |
| cot_full | 4/14 (29%) | 13/14 | 7.78s |
| cot_selective | 6/14 (43%) | 14/14 | 11.37s |

**Key findings:**
- Zero-shot + full schema is optimal (50% EX)
- Few-shot examples *hurt* performance (36% vs 50%)
- Chain-of-thought *hurt* performance (29% vs 50%)
- Full schema better than selective despite more tokens
- +7.1pp improvement over EXP-001 baseline (42.9% → 50%)

**New limitations identified:**
- LIM-007: Few-shot examples hurt llama3.1:8b performance
- LIM-008: CoT reasoning scaffold reduces accuracy at 8B scale

### Implementation

**Files created:**
- `app/config.py` — Added prompt variants (GENERIC, FEW_SHOT, COT) and schema type constants
- `app/database.py` — Added `build_schema_text()` for selective schema generation
- `scripts/run_ablation.py` — Ablation experiment runner
- `data/experiments/s02_ablation/README.md` — EXP-002 documentation
- `data/experiments/s02_ablation/ablation_results_20260203_131921.json` — Full results

**Tests added:**
- `TestAblationPrompts` in `test_agent.py` — 4 tests for `get_ablation_prompt()`
- `TestBuildSchemaText` in `test_database.py` — 4 tests for `build_schema_text()`
- Total tests: 41 passing

### DSM Feedback

- Entry 17: Explain Before Acting principle (Gap)
- Entry 18: CLAUDE.md updated with explicit collaboration workflow (Success)
- Entry 19: Use AskUserQuestion tool for approvals (Gap)
- Entry 20: Ablation study counter-intuitive findings (Success)

### Blog Materials

- Updated `blog-materials-s02.md` with ablation results
- Blog Part 3 ready to write: "What 84 Experiments Taught Me About Prompt Engineering"
- Hook: counter-intuitive finding that research-recommended techniques hurt

---

## Files Changed This Session

| File | Action | Description |
|------|--------|-------------|
| `app/config.py` | Modified | Added ablation prompt variants and constants |
| `app/database.py` | Modified | Added `build_schema_text()` function |
| `scripts/run_ablation.py` | Created | EXP-002 experiment runner |
| `tests/test_agent.py` | Modified | Added TestAblationPrompts class |
| `tests/test_database.py` | Modified | Added TestBuildSchemaText class |
| `data/experiments/s02_ablation/README.md` | Created | EXP-002 full documentation |
| `data/experiments/s02_ablation/ablation_results_*.json` | Created | Results data |
| `data/experiments/EXPERIMENTS_REGISTRY.md` | Modified | Added EXP-002 entry |
| `docs/feedback/methodology.md` | Modified | Entries 17-20 |
| `docs/blog/blog-materials-s02.md` | Modified | Ablation results and blog angles |
| `.claude/CLAUDE.md` | Modified | Explicit collaboration workflow |
| `docs/checkpoints/s02_phase2_checkpoint.md` | Created | This file |

---

## Phase 2 Readiness Checklist

- [x] Prompt variants added to config.py (zero-shot, few-shot, CoT)
- [x] Schema context variants implemented (full, selective)
- [x] Ablation experiment runner created
- [x] All 84 experiments run successfully
- [x] Results analyzed and documented in EXP-002 README
- [x] Best configuration identified: zero_shot_full (50% EX)
- [x] DSM feedback documented (Entry 20)
- [x] Blog materials updated with results
- [x] All tests passing (41 tests)

---

## Recommendations for Phase 3

Based on EXP-002 findings:

1. **Use zero_shot_full configuration** — best accuracy (50%), fast (8.97s), 100% valid syntax
2. **Remove selective schema filtering** — adds latency without accuracy benefit
3. **Do not add few-shot examples** — counter to literature but empirically validated
4. **Do not add CoT reasoning** — hurts accuracy at 8B scale
5. **Focus Medium queries** — Easy saturated (80-100%), Hard blocked (0%)

---

## Next Steps (Phase 3: Streamlit UI)

1. Create `app/main.py` — Streamlit entry point
2. Build core UI: NL input → SQL display → results table
3. Add error handling and Ollama status check
4. Add database selector (Chinook default + SQLite upload)
5. Test full flow: "How many employees are there?" → 8

---

## Commit Message

```
EXP-002: Complete ablation study - zero_shot_full wins (50% EX)

- Add prompt variants: zero-shot, few-shot, CoT (app/config.py)
- Add schema context: build_schema_text() for selective filtering
- Create ablation runner: scripts/run_ablation.py (84 runs)
- Document findings: counter-intuitive results where simpler prompts win
- Update tests: 8 new tests for ablation functions (41 total)

Key findings:
- Zero-shot + full schema: 50% EX (best)
- Few-shot hurt: 36% EX (-14pp)
- CoT hurt: 29% EX (-21pp)
- +7.1pp improvement vs EXP-001 baseline

New limitations: LIM-007 (few-shot hurts 8B), LIM-008 (CoT hurts 8B)
```
