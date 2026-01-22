# SQL Query Agent with Ollama

A natural language to SQL query application powered by open-source LLMs running locally via [Ollama](https://ollama.ai/).

## Overview

This project enables users to query SQL databases using plain English. Instead of writing SQL manually, simply ask questions like:

- "How many customers are in each country?"
- "What are the top 5 best-selling products?"
- "Show me all orders from last month with total over $100"

The agent translates your question into SQL, executes it, and returns the results.

## Features

- **Local LLM**: Runs entirely on your machine using Ollama (no API keys needed)
- **Natural Language Interface**: Ask questions in plain English
- **SQL Generation**: Automatically generates and executes SQL queries
- **Schema Awareness**: Understands your database structure for accurate queries
- **Streamlit UI**: User-friendly web interface (coming in Sprint 2)

## Tech Stack

- **LLM Runtime**: [Ollama](https://ollama.ai/)
- **Framework**: [LangChain](https://python.langchain.com/) (SQL Agent)
- **Frontend**: Streamlit
- **Database**: SQLite (with potential for PostgreSQL/MySQL support)
- **Language**: Python 3.10+

## Recommended Models

| Model | Size | Notes |
|-------|------|-------|
| `llama3.1:8b` | 4.7GB | Good balance of speed and quality |
| `codellama:13b` | 7.4GB | Code-focused, better SQL syntax |
| `mistral:7b` | 4.1GB | Fast, decent SQL generation |
| `sqlcoder:7b` | 4.1GB | Specialized for SQL |

## Project Status

This project is under active development.

- [ ] **Sprint 1**: Jupyter notebook experimentation
- [ ] **Sprint 2**: Streamlit application

See [PLAN.md](PLAN.md) for the detailed development roadmap.

## Getting Started

### Prerequisites

1. Install [Ollama](https://ollama.ai/)
2. Pull a model:
   ```bash
   ollama pull llama3.1:8b
   ```
3. Python 3.10+

### Installation

```bash
# Clone the repository
git clone https://github.com/albertodiazdurana/sql-query-agent-ollama.git
cd sql-query-agent-ollama

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Usage

*Coming soon - see Sprint 1 notebook for experimentation*

## Project Structure

```
sql-query-agent-ollama/
├── app/                  # Streamlit application (Sprint 2)
├── notebooks/            # Jupyter notebooks for experimentation
├── data/                 # Sample databases
├── requirements.txt
├── PLAN.md              # Development roadmap
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
