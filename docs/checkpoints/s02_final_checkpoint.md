# Sprint 2 Final Checkpoint

**Date:** 2026-02-03
**Sprint:** 2 of 2 (Final)
**Status:** Complete

---

## Summary

Sprint 2 transformed the notebook prototype into a production-ready Streamlit application with Docker support. All MUST requirements completed. Key wins: ablation study revealed counter-intuitive prompt engineering findings, and the app runs fully locally with no external API dependencies.

---

## Deliverables

### Phase 1: Code Extraction
- [x] `app/__init__.py` - Package marker
- [x] `app/config.py` - Configuration, prompts, constants
- [x] `app/database.py` - DB engine, schema introspection, post-processing
- [x] `app/agent.py` - AgentState, 6 nodes, graph builder
- [x] `tests/conftest.py` - Shared fixtures
- [x] `tests/test_database.py` - 16 tests
- [x] `tests/test_agent.py` - 17 tests
- [x] Post-processing as separate graph node (LIM-003 fixed)

### Phase 2: Ablation Study (EXP-002)
- [x] 6 configurations tested (3 prompts x 2 schema types)
- [x] 84 experimental runs (6 configs x 14 queries)
- [x] Results: zero-shot + full schema best (50% EX)
- [x] Counter-intuitive finding: few-shot and CoT hurt performance
- [x] +7.1pp improvement over EXP-001 baseline
- [x] LIM-007, LIM-008 identified (few-shot/CoT hurt 8B models)

### Phase 3: Streamlit UI
- [x] `app/main.py` - Full Streamlit application
- [x] Natural language input with SQL generation
- [x] Schema explorer with relationship diagram
- [x] Table details with column types and foreign keys
- [x] Query history in sidebar
- [x] Ollama connectivity check
- [x] Error handling (SQL errors, connection errors)

### Phase 4: Docker & Polish
- [x] `Dockerfile` - Python 3.10-slim based image
- [x] `docker-compose.yml` - App + Ollama orchestration
- [x] `.dockerignore` - Build optimization
- [x] Environment variable support (`OLLAMA_BASE_URL`)
- [x] GPU support option (NVIDIA)

---

## Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| App functional | NL → SQL → results | Yes |
| Agent accuracy | >= 42.9% EX | 50% EX (+7.1pp) |
| Test coverage | pytest passes | 33/33 tests |
| Error handling | 3 error types | Yes |
| LIM-003 fixed | Raw vs final SQL | Yes |

---

## Limitations Discovered

| ID | Description | Severity | Disposition |
|----|-------------|----------|-------------|
| LIM-007 | Few-shot examples hurt performance on 8B models | High | Document, use zero-shot |
| LIM-008 | Chain-of-thought hurts performance on 8B models | High | Document, use zero-shot |

---

## Architecture (Final)

```
[schema_filter] → [generate_sql] → [postprocess_query] → [validate_query] → [execute_query] → [END]
                        ^                                       |                    |
                        |                                       v                    v
                        +-------------------------------- [handle_error] <-----------+
                                                         (max 3 retries)
```

---

## Key Decisions

- **DEC-006:** Zero-shot prompting for llama3.1:8b (based on EXP-002 ablation)
- **DEC-007:** Full schema over selective filtering (ablation showed better results)
- **DEC-008:** Docker Compose for deployment (portability without cloud dependency)

---

## Files Changed This Sprint

```
app/
├── __init__.py          (new)
├── agent.py             (new)
├── config.py            (new)
├── database.py          (new)
└── main.py              (new)

tests/
├── conftest.py          (new)
├── test_agent.py        (new)
└── test_database.py     (new)

data/experiments/
├── EXPERIMENTS_REGISTRY.md  (updated)
└── s02_ablation/
    ├── README.md            (new)
    ├── run_ablation.py      (new)
    └── ablation_results_*.json (new)

docs/
├── checkpoints/s02_*.md     (new)
├── feedback/methodology.md  (updated)
└── blog/blog-materials-s02.md (updated)

Root:
├── Dockerfile               (new)
├── docker-compose.yml       (new)
├── .dockerignore            (new)
└── requirements.txt         (updated)
```

---

## Next Steps (Future Work)

1. Model selector dropdown in UI
2. CSV export for results
3. Query editing before execution
4. Test with larger models (15B+) when hardware allows
5. PostgreSQL/MySQL support
