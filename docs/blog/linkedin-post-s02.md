# LinkedIn Post: Blog Part 2 (Collaboration Value)

**Published:** February 2026
**Blog:** The Case for Human-Agent Collaboration: What 28 Test Outputs Taught Me About Cognitive Limits
**Image:** Can-you-see-the-error.png

---

Can you spot the error in this SQL output?

```
Music         487601.71 hours
TV Shows      278386.09 hours
90's Music    110751.43 hours
```

The query is syntactically perfect. It executes without errors. It returns three playlists in the right order. But the numbers are 1000x too high.

The model divided by 3600.0 instead of 3600000.0. Milliseconds to hours, not seconds to hours.

I ran 28 test outputs while evaluating two LLMs for a text-to-SQL agent. Research shows human reviewers detect 50-82% of defects, with efficiency dropping after 2 hours of inspection. After the fifth output, your eyes glaze over.

The AI agent caught this one because it compared every output to pre-computed ground truth. It doesn't get fatigued. It doesn't assume a query worked because it returned data.

But here's the thing: the agent also doesn't know that $64 billion in "drama revenue" is absurd. The human provides domain sanity checks. The methodology provides structure — hypotheses before testing, numbered limitations, auditable artifacts.

The value isn't speed. It's the loop: agent parses and compares, human questions and validates, structured methodology makes errors visible.

Full write-up on what 28 test outputs taught me about cognitive limits and human-agent collaboration.

Link in comments.

#MachineLearning #AIEngineering #SoftwareTesting #DataScience #HumanInTheLoop #LLM

---

## Comment (with blog link)

The methodology mentioned in the post is the Data Science Methodology (DSM) — an open-source framework I'm developing for structured human-AI collaboration on data science and software engineering projects.

If you're the kind of person who likes numbered decision logs, experiment templates with rejection criteria, and limitation registries that feed into sprint backlogs — DSM might be for you.

It's still evolving (this SQL agent project is one of two active case studies), but the core idea is simple: structure makes collaboration auditable. When reasoning is visible in artifacts, you can question it, improve it, and trust it.

DSM Repo: https://github.com/albertodiazdurana/agentic-ai-data-science-methodology
