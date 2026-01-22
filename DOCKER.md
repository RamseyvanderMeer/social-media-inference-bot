# Docker Quick Reference Guide

Quick reference for running the XAI Agentic Workflow in Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- `.env` file with API keys

## Quick Commands

### Setup
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and add your API keys
# Required: GROK_API_KEY, OPENAI_API_KEY

# 3. Build and start
docker-compose build
docker-compose up
```

### Common Operations

```bash
# Start container (interactive mode)
docker-compose up

# Start in background
docker-compose up -d

# Stop container
docker-compose down

# Run single query
docker-compose run --rm agent python run.py query "What are people saying about AI?"

# Run evaluation
docker-compose run --rm agent python run.py evaluate --num-queries 5

# Access shell
docker-compose exec agent bash

# View logs
docker-compose logs -f agent

# Rebuild after changes
docker-compose build --no-cache
```

## File Structure

```
xai/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Compose configuration
├── docker-entrypoint.sh    # Initialization script
├── .dockerignore           # Files to exclude from build
├── .env.example            # Environment template
└── .env                    # Your environment file (create this)
```

## Environment Variables

Create `.env` file with:

```bash
GROK_API_KEY=your_grok_api_key
OPENAI_API_KEY=your_openai_api_key
```

See `.env.example` for all available options.

## Data Persistence

Data is stored in:
- `./data/` - Vector store and mock data
- `./evaluation_results/` - Evaluation outputs

These persist between container restarts.

## Troubleshooting

**Container won't start:**
- Check `.env` file exists and has valid API keys
- Check logs: `docker-compose logs agent`

**Data not persisting:**
- Verify volumes in `docker-compose.yml`
- Check directory permissions

**Need fresh start:**
```bash
docker-compose down -v  # Removes volumes
# Then rebuild and start
```

## Advanced Usage

### Custom Commands

```bash
# Generate data
docker-compose run --rm agent python run.py generate-data

# Setup vector store
docker-compose run --rm agent python run.py setup-vector-store

# Run analysis
docker-compose run --rm agent python analyze_tool_usage.py
docker-compose run --rm agent python analyze_tool_effectiveness.py
```

### Development Mode

Mount source code for live development:

```yaml
# Add to docker-compose.yml volumes:
volumes:
  - ./src:/app/src  # Live code reload
```

### Production

- Use specific image tags
- Set resource limits
- Use secrets management for API keys
- Configure health checks
- Set up logging aggregation

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full production guide.
