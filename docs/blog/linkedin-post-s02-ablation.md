# LinkedIn Post: Blog Part 3 - Ablation Study

**Character count target:** < 3000 (LinkedIn limit)

---

I ran 84 experiments to validate "best practices" for prompt engineering.

The literature recommends: add few-shot examples (+10-15% accuracy), use chain-of-thought reasoning, filter irrelevant schema.

For my 8B local model? None of that transferred.

Here's what happened when I tested 6 prompt configurations on my text-to-SQL agent:

**Results:**
- Zero-shot + full schema: 50% accuracy (WINNER)
- Few-shot + full schema: 36% (-14pp)
- Chain-of-thought: 29% (-21pp)

The simplest approach outperformed the more complex techniques.

**Why few-shot hurt:**
My examples (employee count, album lookup) anchored the model on wrong patterns. When it saw a genre question, it pattern-matched to the simple example instead of figuring out the JOIN it actually needed.

**Why CoT hurt:**
The model spent tokens explaining what it would do, then generated worse SQL. For constrained code generation, explicit reasoning dilutes focus.

**Why full schema won:**
Naive keyword filtering removed tables needed for JOINs. The model can figure out what to ignore — I shouldn't filter for it.

**What I would have shipped without this data:**
- Few-shot as default → 36% accuracy
- Instead of → 50% accuracy
- 14 percentage points left on the table

The ablation took 15 minutes. It changed my default configuration.

**The lesson:** Research findings are averages across models and datasets. Your specific combination may behave differently. The only way to know is to measure.

If you're building with local 8B models:
1. Start with zero-shot
2. Test few-shot carefully — bad examples are worse than none
3. Skip CoT for code generation
4. Provide full context
5. Measure before shipping

Full blog post with methodology and references:
https://github.com/albertodiazdurana/sql-query-agent-ollama/blob/main/docs/blog/blog-s02-ablation.md

#PromptEngineering #LLMs #TextToSQL #MachineLearning #AblationStudy #DataScience

---

**Post URL:** (to be filled after publishing)
