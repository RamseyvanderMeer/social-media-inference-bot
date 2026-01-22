# Autonomous Multi-Step Agentic Workflow with Grok

An autonomous agentic workflow system that uses Grok as the central reasoner for complex research on simulated X (Twitter) data. The system implements an iterative loop: **plan → decompose → select tools → analyze → refine → summarize**, with robust context management and Grok-driven replanning for ambiguity.

## Features

- **Autonomous Planning**: Grok generates detailed plans for answering complex queries
- **Hybrid Retrieval**: Combines semantic and keyword search for optimal results
- **Tool Integration**: Search, sentiment analysis, entity extraction, and summarization tools
- **Context Management**: Sliding window with compression for efficient context handling
- **Replanning**: Automatic detection of ambiguity and replanning when needed
- **Evaluation Framework**: Comprehensive metrics for testing and comparison

## Architecture

The system is built with a modular, chunk-based architecture:

- **Data Layer**: Mock X data generation and loading
- **Vector Store**: ChromaDB with LlamaIndex for semantic search
- **Retrieval**: Hybrid semantic + keyword search
- **Tools**: Registry of agent tools (search, analysis, summarization)
- **Agent**: Orchestrator with Grok integration via LlamaIndex
- **Context**: Sliding window context manager with compression
- **Replanning**: Ambiguity detection and automatic replanning

## Quick Start

### Prerequisites

- Python 3.12+
- Grok API key
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd xai
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GROK_API_KEY
```

5. Generate mock data:
```bash
python run.py generate-data
```

6. Set up vector store:
```bash
python run.py setup-vector-store
```

### Usage

#### Interactive Mode
```bash
python run.py interactive
```

#### Single Query
```bash
python run.py query "What are people saying about AI?"
```

#### Run Evaluation
```bash
python run.py evaluate --num-queries 30 --output-dir evaluation_results
```

## Configuration

Configuration is managed through environment variables (see `.env.example`):

- `GROK_API_KEY`: Your Grok API key (required)
- `GROK_API_BASE_URL`: Grok API base URL (default: https://api.x.ai/v1)
- `GROK_MODEL`: Grok model to use (default: grok-beta)
- `CHROMA_DB_PATH`: Path to ChromaDB database
- `MAX_ITERATIONS`: Maximum agent iterations (default: 10)
- `CONTEXT_WINDOW_SIZE`: Context window size (default: 10)

## Project Structure

```
xai/
├── src/
│   ├── agents/          # Agent orchestration and Grok client
│   ├── config/          # Configuration management
│   ├── data/            # Data generation and loading
│   ├── tools/           # Tool registry and retrieval
│   ├── evaluation/      # Evaluation framework
│   └── cli.py          # CLI interface
├── data/                # Data files
├── tests/               # Test suite
├── docs/                # Documentation
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
└── docker-compose.yml   # Docker Compose configuration
```

## Docker Deployment

### Build and Run

```bash
# Build image
docker-compose build

# Run container
docker-compose up
```

### Environment Variables

Set environment variables in `docker-compose.yml` or use a `.env` file.

## Evaluation

The evaluation framework tests the agent with diverse queries and measures:

- **Completion Rate**: Percentage of successful queries
- **Step Efficiency**: Average steps and time per query
- **Summary Quality**: Completeness and length metrics

Results are exported to JSON and CSV formats.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
```

### Type Checking

```bash
mypy src/
```

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and architecture
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guide
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues and solutions

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
