# Experiments Registry

**Project:** SQL Query Agent with Ollama
**DSM Reference:** Appendix C.1.6 (Experiment Artifact Organization)

---

| ID | Name | Sprint | Day | Date | Result | Folder |
|----|------|--------|-----|------|--------|--------|
| EXP-001 | Text-to-SQL Model Comparison: sqlcoder:7b vs llama3.1:8b | 1 | 2 | 2026-02-02 | COMPLETE — Both 42.9% EX; llama3.1:8b recommended (faster, no hallucination) | `s01_d02_exp001/` |
| EXP-002 | Prompt Engineering Ablation Study | 2 | 1 | 2026-02-03 | COMPLETE — zero_shot_full best (50% EX); few-shot and CoT hurt performance | `s02_ablation/` |
