# DSM Feedback: Backlog Proposals

**Project:** SQL Query Agent with Ollama
**DSM Version Used:** DSM 1.0 v1.1
**Author:** Alberto
**Date:** 2026-02-01

---

## Medium Priority

### Add research/literature review step to DSM_0
- **DSM Section:** DSM_0_START_HERE_Complete_Guide.md
- **Problem:** DSM_0 jumps straight from project setup to sprint planning. Projects that benefit from surveying state of the art (e.g., ML/AI projects) have no designated step for research before planning.
- **Proposed Solution:** Add an optional "Phase 0: Research" step between project setup and sprint planning in DSM_0, with guidance on when it applies (e.g., novel technique, unfamiliar domain, model selection needed).
- **Evidence:** We added a research phase that produced `docs/research/text_to_sql_state_of_art.md`, which fundamentally changed our architecture (added schema filtering, sqlglot validation, model selection). Without it, the plan would have been less informed.

### Add sprint-level plan template to PM Guidelines
- **DSM Section:** DSM_2.0_ProjectManagement_Guidelines_v2_v1.1.md
- **Problem:** Current templates (1-7) are oriented toward daily task breakdowns. Multi-sprint projects need a sprint-level planning template with phases, readiness checklists, and priority frameworks combined.
- **Proposed Solution:** Add a "Template 8: Sprint Plan" that combines elements from Templates 1 (task breakdown), 4 (prerequisites), and 7 (MUST/SHOULD/COULD) at the sprint level.
- **Evidence:** We had to manually combine three templates to create `docs/plans/sprint-1-plan.md`. A dedicated sprint template would save this synthesis effort.

### Clarify naming and relationship between Validation Tracker and Feedback files
- **DSM Section:** Section 6.4.5 + Appendix E.12
- **Problem:** The Validation Tracker (E.12) scores DSM sections, logs gaps, and proposes recommendations. The feedback backlogs file (6.4.5) also captures DSM gaps and improvement proposals. The overlap is significant and the naming ("validation" vs "feedback") doesn't clarify the distinction. Section 6.4.5 says they are "distinct" but in practice the tracker's recommendations directly feed into backlogs.
- **Proposed Solution:** Either (a) merge them into a single feedback system with a clear during-execution vs end-of-project distinction, or (b) rename for clarity: "DSM Usage Log" (runtime tracking) vs "DSM Feedback" (structured deliverables).
- **Evidence:** During project setup, we created both and immediately noticed the overlap, leading to confusion about where to log what.

### Add notebook collaboration protocol to Custom Instructions
- **DSM Section:** DSM_Custom_Instructions_v1.1.md + Section 6.2.5 + Section 7.1
- **Problem:** DSM 1.0 describes the cell-by-cell principle (Sections 6.2.5, 7.1) -- execute one cell, validate output, proceed. But neither the Custom Instructions nor these sections specify the actual interaction mechanics: how does the AI agent deliver cells to the user? The agent's default behavior was to write the .ipynb file directly, which bypasses the human-in-the-loop validation that cell-by-cell execution requires. The user had to explicitly correct this and state the protocol.
- **Proposed Solution:** Add a "Notebook Collaboration Protocol" to the Custom Instructions that specifies: (1) the agent provides cells as code/markdown blocks in the conversation, (2) the user pastes into the notebook and executes, (3) the user shares the output back, (4) the agent reads and validates output before providing the next cell, (5) the agent must not write .ipynb files directly during notebook work.
- **Evidence:** The agent attempted to create `notebooks/01_sql_agent_exploration.ipynb` directly via file write. The user rejected this and stated the correct protocol. This is a fundamental interaction pattern for DSM 1.0 notebook projects that should be documented to prevent this misunderstanding on every new project.

### Add docs/checkpoints/ to DSM_0 project structure template
- **DSM Section:** DSM_0_START_HERE_Complete_Guide.md (project structure) + PM Guidelines Template 5 (line 493)
- **Problem:** PM Guidelines Template 5 specifies `docs/checkpoints/` as the checkpoint location. DSM Section 6.4.1 requires milestone checkpoints. But the DSM_0 project structure template does not include a `checkpoints/` folder, so projects discover this gap only when they try to create their first checkpoint.
- **Proposed Solution:** Add `docs/checkpoints/` to the standard project directory structure in DSM_0, alongside `docs/plans/` and `docs/decisions/`.
- **Evidence:** We followed DSM_0 to set up our directory structure, then discovered we needed `docs/checkpoints/` when creating the setup milestone checkpoint.

---

## Low Priority

(To be populated as project progresses)
