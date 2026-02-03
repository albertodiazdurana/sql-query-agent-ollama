# LinkedIn Post: Blog Part 1

**Published:** February 2026
**Blog:** Two Experiments in Parallel: Building a Text-to-SQL Agent While Testing a Collaboration Methodology

---

I expected the SQL-specialized model to win. It didn't.

Running two open-source LLMs locally (sqlcoder:7b vs llama3.1:8b) on a text-to-SQL task, the fine-tuned model matched the general-purpose one on accuracy — 42.9% each.

But the numbers underneath told a different story:

The general-purpose model produced valid SQL 100% of the time. Zero hallucinated tables. Nearly twice as fast. Its failures were all logic errors — predictable and debuggable.

The specialized model invented tables that didn't exist (payment, media_type, invoiceintrack). Two queries crashed from context overflow. Diverse failure modes are harder to fix than consistent ones.

SQL fine-tuning at small scale added risk without adding accuracy.

This came from a structured experiment — hypotheses defined before testing, pre-computed ground truth, error categorization that maps failures to fixes. The methodology forced us to actually check assumptions instead of confirming them.

Full write-up covers the architecture, evaluation framework, and what we learned about local LLMs for code generation.

Link in comments.

#MachineLearning #NLP #DataScience #LLM #TextToSQL #OpenSource

---

## Comment (with blog link)

Blog: https://github.com/albertodiazdurana/sql-query-agent-ollama/blob/main/docs/blog/blog-s01.md

The project repo includes the full experiment report, decision logs, and the evaluation harness if you want to run the same comparison on different models.

Repo: https://github.com/albertodiazdurana/sql-query-agent-ollama
