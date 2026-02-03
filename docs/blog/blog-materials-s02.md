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

## Blog Part 3: Ablation Study (Ready to Write)

**Working Title:** "What 84 Experiments Taught Me About Prompt Engineering — And Why the Research Was Wrong"

### Hook: Counter-Intuitive Results

The literature says: add few-shot examples (+10-15% accuracy), use chain-of-thought reasoning, filter schema to reduce noise. Our data says: **the opposite**.

### Results Summary (EXP-002)

| Configuration | EX | VV | Latency |
|--------------|-----|-----|---------|
| **zero_shot_full** | **7/14 (50%)** | 14/14 | 8.97s |
| zero_shot_selective | 6/14 (43%) | 13/14 | 12.17s |
| few_shot_full | 5/14 (36%) | 14/14 | 8.46s |
| few_shot_selective | 6/14 (43%) | 14/14 | 11.54s |
| cot_full | 4/14 (29%) | 13/14 | 7.78s |
| cot_selective | 6/14 (43%) | 14/14 | 11.37s |

**Winner:** Zero-shot with full schema (50% EX)
**Loser:** Chain-of-thought with full schema (29% EX)
**Delta:** 21 percentage points — enormous for a prompt-only change

### Key Findings

1. **Few-shot examples hurt:** Adding 2 examples *reduced* accuracy by 14pp (50% → 36%)
2. **CoT reasoning hurt:** The reasoning scaffold was the worst performer (29%)
3. **More context is better:** Full schema beat selective despite adding "noise"
4. **Baseline improvement:** 50% EX vs 42.9% EXP-001 baseline (+7.1pp)

### Why This Happened (Hypothesis)

- **Few-shot examples anchored on wrong patterns:** The static examples (employee count, AC/DC albums) may have misled the model on unrelated queries
- **CoT consumed context without adding value:** The reasoning scaffold diluted focus on SQL generation
- **Selective filtering removed needed tables:** The keyword-based filter cut tables required for JOINs

### Research Context

From `docs/research/ablation-study-design.md`:

**AbGen Framework (ACL 2025):**
- Importance, Faithfulness, Soundness criteria
- Our findings: llama3.1:8b behaves differently than GPT-4o

**Spider Benchmark:**
- Few-shot typically +10-20% at 7B scale — not observed here
- Model-specific behavior matters more than general patterns

### Blog Angles

1. **Counter-intuitive finding:** "The research was wrong (for this model)" — lead with surprise
2. **Empirical validation:** "Why I ran 84 experiments instead of trusting the literature"
3. **Null results are results:** "What happens when prompt engineering fails"
4. **Practical recommendation:** "Start simple — zero-shot + full context"

### Data Collected

- [x] EX scores for each configuration
- [x] Latency measurements
- [x] Syntax validity (VV) scores
- [x] Best vs worst configuration delta (21pp)
- [x] Comparison with EXP-001 baseline (+7.1pp improvement)

### Artifacts

- Results JSON: `data/experiments/s02_ablation/ablation_results_20260203_131921.json`
- Experiment README: `data/experiments/s02_ablation/README.md`
- Research notes: `docs/research/ablation-study-design.md`

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
