# Blog Process Effectiveness

**Project:** SQL Query Agent with Ollama
**Author:** Alberto
**DSM Sections Referenced:** 2.5.6 (Blog Deliverable Process), 2.5.7 (Publication Strategy), 2.5.8 (Blog Post as Standard Deliverable)

---

## Purpose

Track blog materials collected during the project and evaluate how well the DSM blog workflow works in practice. This feeds into the blog post drafts at end of each sprint and the final project blog.

---

## Materials Collected

### Sprint 1

| Material | Description | Status |
|----------|-------------|--------|
| Research findings | Text-to-SQL state of the art survey | Collected |
| Architecture decisions | LangGraph graph design, schema filtering rationale | Collected |
| Prompt format discovery | sqlcoder:7b empty response with generic prompts, fix via model-aware routing | Collected |
| Model comparison (initial) | sqlcoder faster (4s) but ID-only results; llama3.1 slower (17s) but JOINs for names | Collected |
| Model comparison results | EXP-001: Both 42.9% EX, llama3.1:8b recommended (0 hallucination, 100% parsability, 1.7x faster) | Collected |
| Error patterns | 5 error categories: schema_linking, syntax, dialect, hallucination, logic. sqlcoder hallucinated tables; llama3.1 had logic errors only | Collected |
| Error repair observation | handle_error successfully repairs bad SQL but with high latency (~62s) | Collected |
| Screenshots/outputs | Notebook outputs, evaluation tables, my-machine-is-having-a-hard-time.png | Collected |
| Evaluation surprise | SQL-specialized model (sqlcoder) did NOT beat general-purpose (llama3.1) — equal accuracy but worse reliability. Counter-intuitive finding worth highlighting | Collected |
| Notebook-to-script transition | Started eval in notebook, hit namespace bug, extracted to scripts mid-sprint. Good "lessons learned" narrative | Collected |
| DSM experiment framework | Used C.1.3/C.1.5/C.1.6 for structured evaluation. Nearly missed it — user had to redirect. Shows value of methodology | Collected |
| Limitation discovery | 6 formal limitations documented (LIM-001 through LIM-006). 0% Hard accuracy for both models at 7-8B scale | Collected |
| Node-by-node build approach | Built and tested 5 nodes individually before wiring graph — caught prompt issue early | Collected |
| Personal touch: genre exploration | Author likes heavy metal, metal, and blues — used the agent to explore these genres in Chinook. Iron Maiden 132 tracks, Metallica 112. Fun angle for blog narrative | Collected |
| Post-processing discovery | Prompt rules can't override fine-tuned model behavior — needed programmatic dialect normalization (ILIKE, NULLS LAST, column casing) | Collected |
| Iterative debugging narrative | Tried prompt fix → failed → built post-processing → success. Good storytelling arc for blog | Collected |

### Sprint 2

| Material | Description | Status |
|----------|-------------|--------|
| *To be populated in Sprint 2* | | |

---

## DSM Blog Process Assessment

### Section 2.5.6: Blog Deliverable Process (6 steps)
*Assessment after Sprint 1 completion.*

| Step | Description | Followed? | Notes |
|------|-------------|-----------|-------|
| 1. Collect materials throughout | Ongoing capture | Done | 20 materials tracked across Sprint 1 |
| 2. Structure outline | Draft structure | Done | Outline below |
| 3. Write first draft | 1,500-3,000 words | Done | ~2,400 words, collaborative draft with AI agent |
| 4. Review and iterate | Technical accuracy check | Done | 5 passes: flow, citations (13 refs), challenges, audience alignment, style matching |
| 5. Finalize | Publication-ready | Done | `docs/blog/blog-s01.md` — Part 1 of 2 |
| 6. Publish | Short post + article | Done | LinkedIn post published 2026-02-03 with Task Manager screenshot |

### Section 2.5.7: Publication Strategy
*Assessment at project end.*

### Section 2.5.8: Blog Post as Standard Deliverable
*Assessment at project end.*

---

## Blog Topics / Angles

*Ideas captured during development:*

1. "Building a Text-to-SQL Agent with Local LLMs" -- the main project narrative
2. Research-driven development: how surveying state of the art changed the architecture
3. Model comparison: SQL-specialized vs general-purpose LLMs for code generation
4. Evaluation methodology for LLM-generated code
5. "The SQL-specialized model didn't win" — counter-intuitive finding about fine-tuning vs general-purpose at small scale

---

## Sprint 1 Blog Outline

**Working title:** "Building a Text-to-SQL Agent with Local LLMs: What I Learned from Evaluating sqlcoder vs llama3.1"

### Structure

1. **Introduction** — The problem: querying databases with natural language, no cloud APIs
   - Why local LLMs (privacy, cost, control)
   - Why SQL as a testbed for code generation

2. **Research-Driven Design** — How surveying the state of the art changed the architecture
   - Key findings from DIN-SQL, MAC-SQL, CHESS
   - Schema filtering as most impactful sub-task
   - Structured graph > ReAct for small models

3. **Building the Agent** — The 5-node LangGraph architecture
   - Node-by-node build approach (test individually, then wire)
   - The prompt format discovery (sqlcoder's empty responses)
   - The post-processing story: prompt rules can't override fine-tuning
   - Personal angle: exploring Heavy Metal in the Chinook database

4. **The Evaluation** — Systematic model comparison
   - 14-query test suite design (Easy/Medium/Hard)
   - Adapting Spider EX metric for local evaluation
   - The surprising result: both models at 42.9%

5. **The Counter-Intuitive Finding** — SQL-specialized ≠ better
   - sqlcoder: hallucinated tables, context overflow, slower
   - llama3.1: 100% parsability, zero hallucination, faster
   - At 7-8B scale, fine-tuning adds risk without adding accuracy
   - The model recommendation and why

6. **Lessons Learned**
   - 0% Hard accuracy: the 7B parameter wall
   - Notebook-to-script transition: knowing when to leave the notebook
   - What Sprint 2 will focus on (few-shot, better schema filtering, Streamlit UI)

7. **Conclusion** — Local LLMs are viable for simple-to-medium SQL. The gap is well-understood and the improvement roadmap is clear.

---

## Observations on DSM Blog Workflow

1. Collecting materials throughout the sprint worked well — having a running list made the outline easy to write.
2. The blog file was initially placed in `docs/feedback/` (following Section 6.4.5 grouping) but moved to `docs/blog/` at sprint boundary. Blog materials are project output, not DSM feedback.
3. The "collect → outline → draft" flow from Section 2.5.6 is logical. Sprint 1 completed steps 1-2. Steps 3-6 completed during Sprint 2 Phase 1.
4. Writing the draft was collaborative: AI agent wrote first draft from materials, author reviewed and iterated section by section. Five refinement passes, each targeting one concern (flow, citations, challenges, audience alignment, style).
5. Using the previous LinkedIn post (disaster tweets) as a style reference ensured consistency across posts. This "style reference" step should be part of the DSM process.
6. The "alignment exercise" — mapping blog content to a target audience's interests without rewriting — surfaced implicit angles and strengthened the post naturally.
7. LinkedIn post was adapted from the blog (short-form version of the hook + key finding). Link placed in first comment, not post body (algorithm preference). Task Manager screenshot used as image.

---

## Emerging Blog Style Guide

*Conventions observed across two blog posts (disaster tweets, SQL agent). To be updated after each post.*

### Long-Form (Blog Article)
- **Byline:** "By Alberto Diaz Durana | [Month] [Year]"
- **Opening:** Hook with surprising or counter-intuitive finding
- **Tone:** Learner sharing discoveries, not authority lecturing. Honest about limitations.
- **Structure:** Setup → Build → Evaluate → Learn → What's Next
- **Citations:** Numbered [1] with full reference list at end. Grounded in research.
- **Formatting:** Tables for metrics/results. Bold for key terms on first use. ASCII or Mermaid diagrams for architecture. No emojis.
- **Closing:** Engagement question inviting reader experience. GitHub links to open-source repos.
- **Length:** 2,000-2,500 words

### Short-Form (LinkedIn Post)
- **Opening:** Counter-intuitive result or expectation vs reality contrast (visible before "see more")
- **Tone:** Same as blog — reflective, educational
- **Formatting:** No emojis. Clean line breaks between concept sections. No bold or special characters.
- **Links:** Blog URL in first comment, NOT in post body (LinkedIn algorithm deprioritizes external links)
- **Image:** Authentic screenshot preferred over polished graphics (relatability > polish)
- **Hashtags:** 6-8 relevant tags at end
- **Length:** 150-200 words
