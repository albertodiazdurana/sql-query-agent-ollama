# Text-to-SQL: State of the Art Research Summary

**Project:** SQL Query Agent with Ollama
**Date:** 2026-02-01
**Purpose:** Inform architecture decisions for Sprint 1 prototype
**Knowledge boundary:** Training data through May 2025, supplemented with web search through February 2026

---

## 1. Key Benchmarks

### Spider (Yale, 2018)
- **Paper:** "Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Database Evaluation of Text-to-SQL" (Yu et al., EMNLP 2018)
- **URL:** https://yale-lily.github.io/spider
- **Size:** 10,181 questions across 200 databases (160 train, 40 test)
- **Key feature:** Cross-database generalization -- models must work on unseen databases
- **Difficulty levels:** Easy, Medium, Hard, Extra Hard (nested queries, GROUP BY, JOINs, set operations)
- **Metrics:** Exact Match Accuracy (EM), Execution Accuracy (EX)
- **Top scores (2024):** ~85-91% EX with GPT-4-based pipelines. Largely saturated.

### Spider 2.0 (2024)
- **Paper:** "Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows" (Lei et al., 2024)
- **URL:** https://arxiv.org/abs/2411.07763 | https://spider2-sql.github.io/
- **Key change:** Enterprise-style SQL with multiple dialects (BigQuery, Snowflake, PostgreSQL), longer schemas, workflow-style queries
- **Top scores (Apr 2025):** ~31% EX. Even o1-preview solves only 17.1%. Exposes the gap between benchmarks and real-world SQL.
- **Spider2-DBT (May 2025):** 68-task subset for quick benchmarking of repository-level text-to-SQL

### BIRD-SQL (NeurIPS 2023)
- **Paper:** "Can LLM Already Serve as A Database Interface?" (Li et al., NeurIPS 2023)
- **URL:** https://bird-bench.github.io/ | arXiv:2305.03111
- **Size:** 12,751 question-SQL pairs over 95 large databases (avg 655K rows)
- **Key differentiator:** Includes "evidence" -- external domain knowledge hints (e.g., "revenue = unit_price * quantity")
- **Metrics:** Execution Accuracy (EX), Valid Efficiency Score (VES)
- **Top scores:** 40% EX (Mar 2023) -> 76% EX (Apr 2025). IBM Granite ExSL+granite-20b-code held top spot at ~68%.
- **Human baseline:** 93% EX -- significant gap remains

### BIRD Extensions (2025)
- **BIRD-Interact (Jun 2025):** Interactive evaluation with conversational and agentic modes. Best: o3-mini at 24.4% (conversational), Claude-3.7-Sonnet at 17.78% (agentic). Discovered Interaction-Time Scaling (ITS).
- **BIRD-Critic / SWE-SQL (Feb 2025):** SQL debugging and reasoning benchmark. Top performers are reasoning-based models.

### WikiSQL (Salesforce, 2017)
- **URL:** https://github.com/salesforce/WikiSQL
- **Size:** 80,654 question-SQL pairs. Single-table, simple SELECT only.
- **Status:** Largely solved (>93% EX). Not a meaningful discriminator.

### Dr.Spider (ICLR 2023)
- Tests robustness to perturbations: schema synonyms, NL paraphrasing, database value changes
- **Key insight:** Many high-scoring Spider systems are brittle -- small perturbations cause large accuracy drops

### Benchmark Selection for This Project
BIRD-style evaluation is recommended over Spider for our 10-15 query test suite: it better represents production scenarios with larger tables, noisy data, and required domain knowledge.

---

## 2. Leading Approaches

### 2A. Prompting Strategies

**DIN-SQL (NeurIPS 2023)**
- **Paper:** arXiv:2304.11015
- **Approach:** Decompose into sub-problems: schema linking -> difficulty classification -> SQL generation (difficulty-specific prompts) -> self-correction
- **Results:** 85.3% EX on Spider (dev) with GPT-4
- **Relevance:** Decomposition maps directly to LangGraph nodes. Classification step is practical for routing simple vs. complex queries.

**DAIL-SQL (VLDB 2024)**
- **Paper:** arXiv:2308.15363
- **Key finding:** Example selection matters enormously. Selects few-shot examples based on question similarity AND SQL skeleton similarity.
- **Results:** 86.6% EX on Spider (test) with GPT-4
- **Practical finding:** 5-10 well-curated examples close much of the gap vs. fine-tuned models.

**C3 (2023)**
- **Paper:** arXiv:2307.07306
- **Approach:** Zero-shot with clear prompting + calibration + consistency (multiple candidates, execution-based voting)
- **Relevance:** Consistency voting is feasible with local Ollama if latency is acceptable.

**MAC-SQL (2023)**
- **Paper:** arXiv:2312.11242
- **Approach:** Three specialized agents: Selector (picks tables/columns), Decomposer (breaks complex questions), Refiner (fixes SQL with execution feedback)
- **Results:** 86.75% EX on Spider (dev) with GPT-4
- **Relevance:** Directly maps to our LangGraph architecture.

**CHESS (2024)**
- **Paper:** arXiv:2405.16755
- **Approach:** Entity/value retrieval (NER + fuzzy matching) -> schema filtering -> SQL generation -> SQL revision
- **Results:** ~73% EX on BIRD with GPT-4
- **Key insight:** Value retrieval (finding actual data values mentioned in the question) is critical and often overlooked.

### 2B. Agent-Based Approaches

**Self-Correction / Reflexion Pattern**
- Most impactful agent pattern: generate SQL -> execute -> observe error -> regenerate with error context
- **Implementation detail:** Feed error message + original question + failed SQL back to the model
- **Improvement:** +5-10% accuracy with 2-3 retries

**Structured Graph vs. ReAct**
- LangChain's `create_sql_agent` uses free-form ReAct tool selection
- **Limitation:** 7B-13B models struggle with ReAct reasoning -- wrong tool order, hallucinated tool names, loops
- **Recommendation:** LangGraph structured graph is better for smaller models. Constrained workflows compensate for model limitations.

**Multi-Agent Trend (2024-2025)**
- Specialized agents: schema agent, query planner, SQL writer, debugger
- For local models: multiple agents = multiple LLM calls. Feasible but consider latency.

### 2C. Schema Linking

Schema linking is the single most important sub-task for text-to-SQL accuracy.

**Approaches (ranked by effectiveness):**
1. LLM-based: Ask the LLM to identify relevant tables/columns before SQL generation
2. Embedding-based: sentence-transformers + FAISS retrieval
3. Keyword + fuzzy matching: edit distance or token overlap
4. Hybrid: keyword matching (precision) + embedding retrieval (recall) + LLM filter

**Schema representation (for code-trained models):**
- Best: `CREATE TABLE` statements with comments and foreign key constraints
- Include 3-5 sample rows per table for value understanding
- Filter to relevant tables for databases with 5+ tables

---

## 3. Open-Source Model Performance

### Approximate Performance Tiers (Spider EX)

| Model | Spider EX | Notes |
|-------|-----------|-------|
| GPT-4 + best prompting | 85-91% | DIN-SQL/DAIL-SQL/CHESS pipelines |
| GPT-4 zero-shot | 72-78% | Without specialized prompting |
| Claude 3.5 Sonnet + prompting | 80-87% | Competitive with GPT-4 |
| SQLCoder-15B (fine-tuned) | 70-75% | Best specialized open-source |
| Llama 3.1 70B + prompting | 70-78% | Competitive with GPT-3.5 |
| SQLCoder-7B (fine-tuned) | 65-70% | Outperforms GPT-3.5 on Defog benchmarks |
| Llama 3.1 8B | 50-60% | Viable with strong prompting + retry |
| Mistral 7B | 48-58% | General purpose, decent baseline |
| CodeLlama 7B | 45-55% | Needs careful prompting |

### SQLCoder Details
- **Source:** https://github.com/defog-ai/sqlcoder
- **Ollama:** https://ollama.com/library/sqlcoder
- **Variants:** 7B, 15B, 34B, 70B. Also `defog-llama3-sqlcoder-8b` (Llama 3 fine-tune)
- **License:** Apache-2 (code), CC BY-SA 4.0 (weights)
- **Key finding (nilenso, 2025):** Local LLMs achieve comparable accuracy to frontier models on easy/moderate tasks. 16GB VRAM sufficient for 14B quantized models. Prompt minimalism + JSON schema brought ~5% improvement.

### Key Findings
1. **Fine-tuned > general purpose:** SQLCoder significantly outperforms general-purpose models of same size
2. **Agentic pipelines narrow the gap:** 7B + retry + schema linking approaches zero-shot performance of much larger models
3. **Quantization impact:** 4-bit (Q4_K_M, Ollama default) loses ~3-5% accuracy vs FP16. Use Q5/Q6 if hardware allows.

---

## 4. Evaluation Metrics

### Standard Metrics

| Metric | Description | Use |
|--------|-------------|-----|
| Execution Accuracy (EX) | Does predicted SQL return same results as gold SQL? | Primary metric |
| Exact Match (EM) | Does predicted SQL match gold SQL structurally? | Secondary, overly strict |
| Valid Efficiency Score (VES) | EX * (gold_time / predicted_time) | Rewards efficient queries |
| Test Suite Accuracy | Tests against multiple equivalent databases | Reduces accidental correctness |

### Recommended Metrics for This Project

1. **Execution Accuracy** -- primary: does the query return correct data?
2. **Parsability Rate** -- % of syntactically valid SQL on first attempt
3. **Retry Rate** -- how often the agent needs error correction loops
4. **Latency** -- time from question to answer (critical for local LLM UX)
5. **Error Categorization** -- classify failures: schema linking, syntax, logic, hallucination

### Test Suite Structure
- Easy (4-5 queries): Single table, simple WHERE, basic aggregation
- Medium (4-5 queries): JOINs, GROUP BY + HAVING, ORDER BY with LIMIT
- Hard (3-5 queries): Multi-table JOINs, subqueries, complex aggregation, string matching

---

## 5. Best Practices for Local LLMs (7B-13B)

### Prompting

1. **Be extremely explicit.** Smaller models need more guidance. Include rules, schema, and output format constraints.
2. **Few-shot examples are critical.** 3-5 examples improve accuracy 10-20% for 7B models. Select by question + SQL pattern similarity.
3. **Chain-of-thought hurts small models.** Direct generation with clear instructions works better than "think step by step."
4. **Temperature = 0 always.** SQL is deterministic.
5. **Structured output constraints.** Post-process to extract SQL from markdown/explanations. Use stop tokens.
6. **Set num_ctx.** Ollama default (2048) is too small. Use `num_ctx=8192` via `ChatOllama(model="sqlcoder:7b", num_ctx=8192)`.

### Common Failure Modes

| Failure Mode | Frequency | Mitigation |
|-------------|-----------|------------|
| Hallucinated table/column names | Very common (30%+) | Schema linking, validate against actual schema |
| Wrong JOIN conditions | Common | Include FK constraints, JOIN examples |
| Incorrect aggregation | Common | GROUP BY examples in few-shot |
| SQL dialect errors | Moderate | Specify "Generate SQLite SQL" explicitly |
| Over-complex queries | Moderate | Instruct "generate simplest SQL" |
| String matching issues | Common | Provide sample values or use value retrieval |
| Infinite retry loops | Agent-specific | Cap retries at 3 |

---

## 6. Architectural Recommendations

### Model Priority
1. `sqlcoder:7b` (or `sqlcoder:15b` if VRAM allows) -- purpose-built
2. `mannix/defog-llama3-sqlcoder-8b` -- Llama 3 fine-tune variant
3. `llama3.1:8b` -- general purpose comparison baseline

### Enhanced Agent Architecture

```
[schema_filter] -> [generate_sql] -> [validate_query] -> [execute_query] -> [END]
                        ^                  |                    |
                        |                  v                    v
                        +--------- [handle_error] <-----------+
                                   (max 3 retries)
```

Additions vs. original plan:
- **Schema filtering node:** Prune irrelevant tables before generation (even keyword matching helps)
- **SQL validation node:** Use `sqlglot` to parse/validate syntactically before execution. Check referenced tables/columns exist.
- **Post-processing:** Clean LLM output (extract SQL from markdown, remove explanatory text)

### Prompt Template (optimized for 7B)

```python
SYSTEM_PROMPT = """You are a SQLite expert. Generate a SELECT query to answer the user's question.

Rules:
- Output ONLY a valid SQLite SELECT statement
- Use only the tables and columns listed in the schema
- Never use INSERT, UPDATE, DELETE, DROP, or ALTER
- Use table aliases for any JOINs
- Add LIMIT 100 unless counting or aggregating"""

USER_PROMPT = """Schema:
{filtered_schema}

{few_shot_examples}

Question: {question}

SQL:"""
```

---

## 7. Tools and Libraries

| Tool | Purpose | URL |
|------|---------|-----|
| LangChain SQL Toolkit | SQL agent with tools | https://python.langchain.com/docs/tutorials/sql_qa/ |
| LangGraph | Stateful agent graphs | https://langchain-ai.github.io/langgraph/ |
| Defog SQLCoder | Fine-tuned SQL model | https://github.com/defog-ai/sqlcoder |
| Vanna.ai | Text-to-SQL with RAG | https://github.com/vanna-ai/vanna |
| SQLGlot | SQL parser/transpiler | https://github.com/tobymao/sqlglot |
| sql-metadata | Extract tables/columns from SQL | https://github.com/macbre/sql-metadata |

---

## 8. Key Papers

| Paper | Year | Key Contribution | Reference |
|-------|------|-----------------|-----------|
| DIN-SQL | 2023 | Decomposed prompting + self-correction | arXiv:2304.11015 |
| DAIL-SQL | 2023 | Systematic prompting; example selection | arXiv:2308.15363 |
| MAC-SQL | 2023 | Multi-agent: Selector/Decomposer/Refiner | arXiv:2312.11242 |
| CHESS | 2024 | Value retrieval + schema filtering | arXiv:2405.16755 |
| C3 | 2023 | Zero-shot with calibration + consistency | arXiv:2307.07306 |
| BIRD Benchmark | 2023 | Realistic benchmark with domain knowledge | arXiv:2305.03111 |
| Spider 2.0 | 2024 | Enterprise-complexity benchmark | arXiv:2411.07763 |
| Dr.Spider | 2023 | Robustness evaluation | ICLR 2023 |
| How to Prompt LLMs for Text-to-SQL | 2023 | Comprehensive prompting study | arXiv:2305.11853 |
| Next-Generation Database Interfaces | 2024 | Survey of LLM-based text-to-SQL | arXiv:2406.08426 |
| Annotation Errors Break Benchmarks | 2026 | Leaderboard reliability concerns | arXiv:2601.08778 |

---

## Sources (Web Search, 2026-02-01)

- [Spider 2.0](https://spider2-sql.github.io/)
- [BIRD-bench](https://bird-bench.github.io/)
- [Text-to-SQL: Comparison of LLM Accuracy in 2026](https://research.aimultiple.com/text-to-sql/)
- [Text2SQL Leaderboard | OpenLM.ai](https://openlm.ai/text2sql-leaderboard/)
- [IBM Granite text-to-SQL](https://research.ibm.com/blog/granite-LLM-text-to-SQL)
- [SQLCoder on Ollama](https://ollama.com/library/sqlcoder)
- [Defog SQLCoder GitHub](https://github.com/defog-ai/sqlcoder)
- [defog-llama3-sqlcoder-8b on Ollama](https://ollama.com/mannix/defog-llama3-sqlcoder-8b)
- [Experimenting with Self-Hosted LLMs for Text-to-SQL (nilenso, 2025)](https://blog.nilenso.com/blog/2025/05/27/experimenting-with-self-hosted-llms-for-text-to-sql/)
- [Annotation Errors Break Text-to-SQL Benchmarks](https://arxiv.org/html/2601.08778)
- [Analysis of Text-to-SQL Benchmarks (EDBT 2025)](https://openproceedings.org/2025/conf/edbt/paper-41.pdf)
