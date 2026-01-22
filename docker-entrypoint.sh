#!/bin/bash
set -e

echo "Starting XAI Agentic Workflow container..."

# Check if required environment variables are set
if [ -z "$GROK_API_KEY" ]; then
    echo "ERROR: GROK_API_KEY environment variable is not set"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY environment variable is not set"
    exit 1
fi

# Create necessary directories if they don't exist
mkdir -p /app/data
mkdir -p /app/evaluation_results

# Check if data file exists, generate if not
if [ ! -f "/app/data/mock_x_data.json" ]; then
    echo "Data file not found. Generating mock data..."
    python run.py generate-data
fi

# Check if vector store exists, set up if not
if [ ! -d "/app/data/chroma_db" ] || [ -z "$(ls -A /app/data/chroma_db 2>/dev/null)" ]; then
    echo "Vector store not found. Setting up vector store..."
    python run.py setup-vector-store
fi

# Execute the command passed to the container
echo "Container initialization complete. Executing: $@"
exec "$@"
