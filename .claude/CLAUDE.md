@D:/data-science/agentic-ai-data-science-methodology/DSM_Custom_Instructions_v1.1.md

# Project: SQL Query Agent with Ollama

**Type:** Hybrid (Notebooks + Application)
**Author:** Alberto
**DSM Track:** DSM 1.0 for Sprint 1 (notebook experimentation), DSM 4.0 for Sprint 2 (Streamlit app)

---

## Project Context

- **Purpose**: Build a natural language to SQL query application powered by open-source LLMs running locally via Ollama
- **Framing**: Text-to-code generation testbed -- SQL is a constrained language, making it ideal for systematic evaluation before tackling general-purpose code generation
- **Deliverables**: Sprint 1 = Jupyter notebook prototype with evaluation; Sprint 2 = Streamlit application
- **Users**: Developers and analysts who want to query SQL databases using plain English without writing SQL manually

## Technical Stack

- **LLM Runtime**: Ollama (local, no API keys)
- **Agent Framework**: LangChain + LangGraph
- **Frontend**: Streamlit (Sprint 2)
- **Database**: SQLite (primary), potential PostgreSQL/MySQL support
- **Language**: Python 3.10+
- **Key packages**: `langchain`, `langchain-community`, `langchain-ollama`, `langgraph`, `sqlalchemy`, `sqlglot`, `streamlit`, `jupyter`

## Project Structure

```
sql-query-agent-ollama/
├── .claude/              # AI agent configuration
├── app/                  # Streamlit application (Sprint 2)
│   ├── __init__.py
│   ├── main.py           # Streamlit entry point
│   ├── agent.py          # SQL agent logic
│   ├── database.py       # Database connection handling
│   └── config.py         # Configuration management
├── notebooks/            # Jupyter notebooks (Sprint 1)
├── data/                 # Sample databases
├── docs/
│   ├── plans/
│   │   └── PLAN.md          # Development roadmap (sprints, architecture, evaluation)
│   ├── decisions/
│   ├── checkpoints/         # Milestone checkpoints (PM Guidelines Template 5)
│   ├── research/            # State-of-art research, references
│   ├── backlog/             # DSM-to-project alignment reports (read at session start)
│   ├── feedback/            # Project-to-DSM feedback: backlogs.md, methodology.md, blog.md
│   └── blog/                # Blog materials and drafts
├── tests/                # Tests (Sprint 2)
├── requirements.txt
└── README.md
```

## Environment

- **Platform**: WSL Ubuntu on Windows
- **Project path (WSL)**: `/home/berto/sql-query-agent-ollama/`
- **Project path (Windows)**: `\\wsl.localhost\Ubuntu\home\berto\sql-query-agent-ollama\`
- **DSM repository**: `D:\data-science\agentic-ai-data-science-methodology\`
- **Virtual environment**: `venv/` (created, activate with `source venv/bin/activate`)

## Key References

- **DSM Methodology**: `D:\data-science\agentic-ai-data-science-methodology\`
- **DSM 1.0** (notebook work): `DSM_1.0_Data_Science_Collaboration_Methodology_v1.1.md`
- **DSM 4.0** (app development): `DSM_4.0_Software_Engineering_Adaptation_v1.0.md`
- **PM Guidelines**: `DSM_2.0_ProjectManagement_Guidelines_v2_v1.1.md`
- **Development Plan**: `docs/plans/PLAN.md` -- sprint details, architecture, models, evaluation metrics, code snippets
- **Research**: `docs/research/text_to_sql_state_of_art.md` -- text-to-SQL state of the art, benchmarks, best practices


## Working Style

I always want to understand what we are doing. Before generating any file I want to read a brief explanation what it is and why we need it. This should be the way in which we work: I need to have context to approve.

## Notebook Collaboration Protocol (Sprint 1)

This project uses notebooks in Sprint 1. The following protocol is mandatory:

1. Agent provides ONE cell at a time as a code/markdown block in conversation
2. User copies the cell content into the notebook and runs it
3. User pastes the cell output back into the conversation
4. Agent reads and validates the output (checks shapes, values, errors)
5. Agent provides the next cell only after validating the previous output

**Rules:**
- Never write or modify `.ipynb` files directly
- Never generate multiple cells in a single message unless explicitly requested with "generate all cells"
- Never ask "Want me to proceed with these next steps?" followed by a list of cells -- just provide the next single cell
- Number code cells with a comment (`# Cell 1`, `# Cell 2`); markdown cells are structural headers and should NOT be numbered
- "Continue" or "yes" = generate the next cell
- If the output reveals an issue, address it before moving forward

**Why:** The human needs to maintain context and control. Batching cells skips validation of intermediate outputs, which can cascade errors and removes the human from the loop.

## App Development Protocol (Sprint 2)

When building Streamlit application code in Sprint 2:
- Guide step by step, explain **why** before each action
- Provide code segments for user to copy/paste
- Wait for confirmation before proceeding to next step
- Build modules incrementally with TDD

## DSM Alignment

- Check `docs/backlog/` at session start for any DSM alignment reports
- Update `docs/feedback/` files (backlogs.md, methodology.md, blog.md) at sprint boundaries
- Follow the sprint boundary checklist: checkpoint, feedback files, decision log, blog entry