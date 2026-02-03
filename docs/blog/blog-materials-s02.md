# Blog Materials: Sprint 2

**Sprint:** 2 (Streamlit Application)
**Status:** In Progress
**DSM Track:** DSM 4.0 (Software Engineering Adaptation)

---

## Published Blog Posts

### Blog Part 1: Building a Text-to-SQL Agent (Sprint 1)

**File:** `blog-s01.md`
**LinkedIn Post:** `linkedin-post-s01.md`
**Blog URL:** https://github.com/albertodiazdurana/sql-query-agent-ollama/blob/main/docs/blog/blog-s01.md
**LinkedIn URL:** https://www.linkedin.com/posts/albertodiazdurana_texttosql-codegeneration-llms-activity-7424243816100036608-as2b
**Title:** "Two Experiments in Parallel: Building a Text-to-SQL Agent While Testing a Collaboration Methodology"

**Key Points:**
- sqlcoder:7b vs llama3.1:8b comparison — both achieved 42.9% EX
- General-purpose model produced 100% valid SQL, zero hallucinated tables
- Fine-tuned model invented non-existent tables (payment, media_type)
- LangGraph 5-node architecture with retry logic
- Methodology: hypotheses before testing, pre-computed ground truth

### Blog Part 2: Human-Agent Collaboration (Sprint 2 Phase 1)

**File:** `blog-s02-collaboration-value.md`
**LinkedIn Post:** `linkedin-post-s02.md`
**Blog URL:** https://github.com/albertodiazdurana/sql-query-agent-ollama/blob/main/docs/blog/blog-s02-collaboration-value.md
**LinkedIn URL:** https://www.linkedin.com/posts/albertodiazdurana_machinelearning-aiengineering-softwaretesting-activity-7424401395388354560-2rbd
**Title:** "The Case for Human-Agent Collaboration: What 28 Test Outputs Taught Me About Cognitive Limits"

**Key Points:**
- Cognitive fatigue in code review (50-82% defect detection rate)
- Fagan inspection metrics: 1.6-3.6 defects/person-hour
- Three error examples: H4 unit conversion, H2 type mismatch, M5 absurd revenue
- Human-in-the-loop: one-cell-at-a-time protocol
- Structured experiment design: DSM C.1.3, C.1.5, DSM 2.3

---

## Blog Part 3: Ablation Study (Planned)

**Working Title:** "What 56 Experiments Taught Me About Prompt Engineering for Text-to-SQL"

### Research Context

From `docs/research/ablation-study-design.md`:

**Text-to-SQL Evaluation Metrics:**
- Execution Accuracy (EX) — primary metric
- Exact Match (EM) — strict, penalizes valid alternatives
- Valid Efficiency Score (VES) — syntax + efficiency
- Test-suite Accuracy (TS) — robustness

**AbGen Framework (ACL 2025):**
- Importance, Faithfulness, Soundness criteria
- GPT-4o and Llama-3.1 show gaps vs human experts

### Ablation Matrix

| Experiment | Variable | Values |
|------------|----------|--------|
| E1 | Prompt structure | Zero-shot, Few-shot, CoT |
| E2 | Few-shot selection | 0, 2, 3 examples |
| E3 | Schema context | Full, Selective |

### Prompt Variants Implemented

**Zero-shot (baseline):**
```
You are a SQL expert. Generate a SQLite-compatible SELECT query...
```

**Few-shot (2 examples):**
```
Example 1: How many employees are there?
SQL: SELECT COUNT(*) FROM Employee;

Example 2: What are the names of all albums by 'AC/DC'?
SQL: SELECT Album.Title FROM Album JOIN Artist...
```

**Chain-of-thought:**
```
Reasoning:
1. Tables needed:
2. Columns to select:
3. Joins/filters/aggregations:
```

### Potential Blog Angles

1. **Counter-intuitive finding angle:** "Few-shot prompting didn't help" (if that's the result)
2. **Systematic comparison angle:** "How to design an ablation study for prompt engineering"
3. **Reproducibility angle:** "Making LLM experiments reproducible with fixed seeds"
4. **Null result angle:** "What happens when prompt engineering doesn't work"

### Data to Collect

- [ ] EX scores for each configuration
- [ ] Latency measurements
- [ ] Error categorization (syntax, table hallucination, logic)
- [ ] Best vs worst configuration delta
- [ ] Confidence intervals / variance

---

## Observations

### Phase 1 → Phase 2 Transition

1. **Tests as documentation:** 33 tests serve as executable specification
2. **Checkpoint discipline:** Pre-implementation checkpoint captures state
3. **Research-driven design:** AbGen paper influenced ablation matrix design

### Emerging Patterns

- (To be filled after ablation runs)

---

## References

1. [AbGen: LLM Ablation Study Design (ACL 2025)](https://aclanthology.org/2025.acl-long.611/)
2. [Nature Scientific Reports - Text-to-SQL Metrics](https://www.nature.com/articles/s41598-025-04890-9)
3. [Promptfoo - Text-to-SQL Evaluation](https://www.promptfoo.dev/docs/guides/text-to-sql-evaluation/)
