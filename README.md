# Autonomous X Research Agent

An agentic research workflow that uses Grok as the main reasoning model for answering questions over simulated X/Twitter-style data.

The system follows a loop that is common in useful AI agents: plan the work, break it into steps, choose tools, retrieve context, analyze results, replan when the answer looks weak, and summarize the final result.

## What It Does

- Uses Grok through a LlamaIndex ReAct agent
- Searches simulated X data with hybrid semantic + keyword retrieval
- Stores embeddings in ChromaDB and retrieves with LlamaIndex
- Tracks context with a sliding window and compression
- Detects ambiguous or low-confidence results and triggers replanning
- Exports evaluation results to JSON and CSV
- Runs locally or through Docker Compose

## Architecture

- `src/agents`: orchestration, Grok client, callbacks, context management, replanning
- `src/tools`: retrieval tools, tool registry, vector store integration
- `src/data`: mock X data generation and loading
- `src/evaluation`: completion rate, latency, step efficiency, and summary quality metrics
- `docs`: architecture, deployment, and troubleshooting notes

## Tech Stack

- Python 3.12
- Grok / xAI API
- LlamaIndex
- ChromaDB
- OpenAI embeddings
- Docker / Docker Compose
- pandas for evaluation exports

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add `GROK_API_KEY` and `OPENAI_API_KEY` to `.env`, then generate data and build the vector store:

```bash
python run.py generate-data
python run.py setup-vector-store
```

Run an interactive session:

```bash
python run.py interactive
```

Run a single query:

```bash
python run.py query "What are people saying about AI?"
```

Run the evaluation suite:

```bash
python run.py evaluate --num-queries 30 --output-dir evaluation_results
```

## Docker

```bash
docker-compose build
docker-compose up
```

The container checks environment variables, generates mock data if needed, sets up the vector store, and starts the interactive agent.

## Why I Built It

I wanted a concrete implementation of an agent that does more than call an LLM once. This repo focuses on the infrastructure around the model: tool use, retrieval quality, context handling, replanning, and evaluation.
