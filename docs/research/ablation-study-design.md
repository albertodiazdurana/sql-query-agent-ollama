# Ablation Study Design: Research Findings

**Date:** 2026-02-03
**Sprint:** S2 Phase 2
**Purpose:** Document research findings on ablation study methodology and text-to-SQL evaluation metrics to inform EXP-002 design.

---

## 1. Text-to-SQL Evaluation Metrics

### Standard Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| **Execution Accuracy (EX)** | Does the SQL produce correct results when executed? | Primary metric — measures end-to-end correctness |
| **Exact Match (EM)** | Does the SQL match ground truth exactly (string comparison)? | Strict metric — penalizes valid alternative queries |
| **Valid Efficiency Score (VES)** | Syntax validity + execution efficiency | Secondary — useful for comparing query quality |
| **Test-suite Accuracy (TS)** | Performance across diverse database scenarios | Robustness — tests generalization |

**Source:** [Trust3 AI - Bridging the Language Gap](https://trust3.ai/blog/bridging-the-language-gap-evaluating-text-to-sql-performance/)

### Metric Limitations

Current metrics have known limitations:
- **EM is too strict:** Penalizes semantically equivalent queries with different syntax (e.g., `WHERE a AND b` vs `WHERE b AND a`)
- **EX has false positives:** A query can return correct results by accident on small test databases
- **Binary scoring:** Doesn't capture partial correctness (e.g., correct tables but wrong aggregation)

**Emerging solutions:** Semantic similarity metrics that compare query structure and execution results at a granular level.

**Source:** [Nature Scientific Reports - Redefining Text-to-SQL Metrics](https://www.nature.com/articles/s41598-025-04890-9)

---

## 2. Ablation Study Methodology

### Definition

An **ablation study** systematically removes or modifies components of a system to measure their individual contribution. In ML/prompt engineering, this means testing variations of:
- Prompt structure (instructions, examples, format)
- Context (schema, few-shot examples, chain-of-thought)
- Model parameters (temperature, context window)

### AbGen Framework (ACL 2025)

AbGen is the first benchmark for evaluating LLM capabilities in designing ablation studies. Key evaluation criteria:

| Criterion | Description |
|-----------|-------------|
| **Importance** | Does the ablated component play a significant role? |
| **Faithfulness** | Does the ablation design accurately reflect the component's function? |
| **Soundness** | Is the experiment logically and practically reproducible? |

**Finding:** GPT-4o and Llama-3.1 show significant performance gaps compared to human experts in ablation study design. Current automated evaluation methods are unreliable for assessing ablation quality.

**Source:** [AbGen: LLM Ablation Study Design (ACL 2025)](https://aclanthology.org/2025.acl-long.611/)

### Prompt Ablation Best Practices

Research on prompt ablation across multiple LLMs reveals:

1. **Structural components matter:** Prompt format (headers, delimiters, instruction placement) significantly affects output quality
2. **Context selection is critical:** Assertion-level context often outperforms full method context — more information isn't always better
3. **Model-specific effects:** Different LLMs respond differently to the same prompt variations

**Source:** [Assertion-Aware Test Code Summarization](https://arxiv.org/pdf/2511.06227)

---

## 3. Reproducibility Considerations

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| **Non-deterministic outputs** | Set temperature=0, use fixed seeds where possible |
| **Prompt sensitivity** | Test prompts systematically, document exact wording |
| **Result variance** | Run multiple trials, report confidence intervals |
| **Environment differences** | Log model version, hardware, dependencies |

### Reproducibility Checklist

- [ ] Fixed random seed / temperature=0
- [ ] Exact prompt text logged
- [ ] Model version and parameters documented
- [ ] Test set fixed (no data leakage)
- [ ] All results logged with timestamps
- [ ] Experiment can be re-run from logged configuration

**Source:** [Promptfoo - Text-to-SQL Evaluation Guide](https://www.promptfoo.dev/docs/guides/text-to-sql-evaluation/)

---

## 4. Application to EXP-002

### Experiment Design

Based on the research, EXP-002 will test three ablation axes:

#### E1: Prompt Structure
| Variant | Description | Hypothesis |
|---------|-------------|------------|
| Zero-shot | Instruction + schema + question | Baseline |
| Few-shot | + 2-3 example Q/A pairs | +10-20% EX improvement |
| Chain-of-thought | + reasoning before SQL | Better on complex queries |

#### E2: Few-shot Selection
| Variant | Description | Hypothesis |
|---------|-------------|------------|
| 0 examples | No few-shot | Baseline |
| 2 examples | Easy + medium difficulty | Balanced guidance |
| 3 examples | Easy + medium + hard | Maximum guidance |

#### E3: Schema Context
| Variant | Description | Hypothesis |
|---------|-------------|------------|
| Full schema | All 11 tables, all columns | Complete but verbose |
| Selective | Only question-relevant tables | Focused, less noise |

### Metrics to Track

| Metric | Type | Why |
|--------|------|-----|
| Execution Accuracy (EX) | Primary | End-to-end correctness |
| Syntax Validity (VV) | Secondary | Catches parse errors |
| Latency (ms) | Informational | User experience impact |

### Expected Outcomes

1. **Few-shot should improve EX** — Research consistently shows few-shot prompting improves task accuracy
2. **CoT may help complex queries** — Chain-of-thought is effective for multi-step reasoning
3. **Selective schema may reduce hallucination** — Less irrelevant context = fewer distractions

### Null Hypothesis

If no configuration improves significantly over baseline (zero-shot + full schema), this is still a valid finding — it would suggest that prompt engineering has limited impact on this task/model combination, and other approaches (fine-tuning, better schema representation) should be explored.

---

## References

1. [AbGen: LLM Ablation Study Design (ACL 2025)](https://aclanthology.org/2025.acl-long.611/)
2. [Redefining Text-to-SQL Metrics (Nature Scientific Reports 2025)](https://www.nature.com/articles/s41598-025-04890-9)
3. [Promptfoo - Text-to-SQL Evaluation Guide](https://www.promptfoo.dev/docs/guides/text-to-sql-evaluation/)
4. [Trust3 AI - Bridging the Language Gap](https://trust3.ai/blog/bridging-the-language-gap-evaluating-text-to-sql-performance/)
5. [Assertion-Aware Test Code Summarization](https://arxiv.org/pdf/2511.06227)
6. [LLM Text-to-SQL Survey](https://arxiv.org/html/2410.06011v1)
7. [AblationMage Tool (EuroMLSys 2025)](https://dl.acm.org/doi/10.1145/3721146.3721957)
