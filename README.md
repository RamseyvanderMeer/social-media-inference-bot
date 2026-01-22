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

The application is fully dockerized and can run in a self-contained environment. All dependencies and setup are handled automatically.

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Grok API key
- OpenAI API key (for embeddings)

### Quick Start

1. **Create environment file:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

2. **Build and run:**
```bash
# Build the Docker image
docker-compose build

# Start the container in interactive mode
docker-compose up
```

3. **The container will automatically:**
   - Check for required environment variables
   - Generate mock data if not present
   - Set up the vector store if needed
   - Start the interactive agent

### Docker Commands

#### Interactive Mode (Default)
```bash
docker-compose up
# or
docker-compose run --rm agent python run.py interactive
```

#### Single Query
```bash
docker-compose run --rm agent python run.py query "What are people saying about AI?"
```

#### Generate Data
```bash
docker-compose run --rm agent python run.py generate-data
```

#### Setup Vector Store
```bash
docker-compose run --rm agent python run.py setup-vector-store
```

#### Run Evaluation
```bash
docker-compose run --rm agent python run.py evaluate --num-queries 5
```

#### Access Container Shell
```bash
docker-compose exec agent bash
```

#### View Logs
```bash
docker-compose logs -f agent
```

#### Stop Container
```bash
docker-compose down
```

### Environment Variables

The container uses environment variables from:
1. `.env` file (recommended)
2. `docker-compose.yml` environment section
3. System environment variables

**Required variables:**
- `GROK_API_KEY`: Your Grok API key
- `OPENAI_API_KEY`: Your OpenAI API key (for embeddings)

**Optional variables:**
- `GROK_API_BASE_URL`: Default: `https://api.x.ai/v1`
- `GROK_MODEL`: Default: `grok-beta`
- `OPENAI_API_BASE_URL`: Default: `https://api.openai.com/v1`
- `OPENAI_MODEL`: Default: `gpt-4o-mini`
- `CHROMA_DB_PATH`: Default: `/app/data/chroma_db`
- `MAX_ITERATIONS`: Default: `10`
- `LOG_LEVEL`: Default: `INFO`

### Data Persistence

The following directories are mounted as volumes for data persistence:
- `./data` → `/app/data` (vector store and mock data)
- `./evaluation_results` → `/app/evaluation_results` (evaluation outputs)

Data persists between container restarts.

### Building from Dockerfile Directly

If you prefer using Docker directly without Compose:

```bash
# Build image
docker build -t xai-agentic-workflow .

# Run container
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/evaluation_results:/app/evaluation_results \
  xai-agentic-workflow
```

### Troubleshooting

**Container fails to start:**
- Check that `.env` file exists and contains valid API keys
- Verify Docker has enough resources (memory, disk space)
- Check logs: `docker-compose logs agent`

**Data not persisting:**
- Ensure volumes are properly mounted in `docker-compose.yml`
- Check file permissions on host directories

**Vector store issues:**
- Delete `./data/chroma_db` and let container recreate it
- Run: `docker-compose run --rm agent python run.py setup-vector-store`

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
