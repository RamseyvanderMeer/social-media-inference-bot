# Deployment Guide

## Local Development Setup

### Prerequisites

- Python 3.12 or higher
- pip package manager
- Grok API key

### Step-by-Step Setup

1. **Clone and Navigate**
```bash
git clone <repository-url>
cd xai
```

2. **Create Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env and add your GROK_API_KEY
```

5. **Generate Mock Data**
```bash
python run.py generate-data
```

6. **Set Up Vector Store**
```bash
python run.py setup-vector-store
```

7. **Test Installation**
```bash
python run.py query "What are people saying about AI?"
```

## Docker Deployment

The application is fully containerized and self-contained. The Docker setup includes:
- Automatic dependency installation
- Environment variable validation
- Automatic data generation if missing
- Automatic vector store setup if needed
- Data persistence via volumes

### Prerequisites

- Docker Engine 20.10 or higher
- Docker Compose 2.0 or higher
- At least 2GB RAM available for Docker
- At least 1GB free disk space

### Quick Start with Docker Compose

1. **Clone and navigate to project:**
```bash
git clone <repository-url>
cd xai
```

2. **Create environment file:**
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - GROK_API_KEY
# - OPENAI_API_KEY
```

3. **Build and start:**
```bash
docker-compose build
docker-compose up
```

The container will automatically:
- Validate environment variables
- Create necessary directories
- Generate mock data if `/app/data/mock_x_data.json` doesn't exist
- Set up vector store if `/app/data/chroma_db` doesn't exist
- Start the interactive agent

### Docker Compose Commands

#### Start in foreground (interactive mode)
```bash
docker-compose up
```

#### Start in background (detached)
```bash
docker-compose up -d
```

#### Stop container
```bash
docker-compose down
```

#### Rebuild after code changes
```bash
docker-compose build --no-cache
docker-compose up
```

#### Run specific commands
```bash
# Single query
docker-compose run --rm agent python run.py query "Your query here"

# Generate data
docker-compose run --rm agent python run.py generate-data

# Setup vector store
docker-compose run --rm agent python run.py setup-vector-store

# Run evaluation
docker-compose run --rm agent python run.py evaluate --num-queries 10

# Run analysis scripts
docker-compose run --rm agent python analyze_tool_usage.py
docker-compose run --rm agent python analyze_tool_effectiveness.py
```

#### Access container shell
```bash
docker-compose exec agent bash
```

#### View logs
```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

#### Clean up
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Using Dockerfile Directly

If you prefer not to use Docker Compose:

1. **Build image:**
```bash
docker build -t xai-agentic-workflow .
```

2. **Run container with environment file:**
```bash
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/evaluation_results:/app/evaluation_results \
  xai-agentic-workflow
```

3. **Run container with inline environment variables:**
```bash
docker run -it --rm \
  -e GROK_API_KEY=your_key \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/evaluation_results:/app/evaluation_results \
  xai-agentic-workflow python run.py interactive
```

4. **Run specific commands:**
```bash
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/evaluation_results:/app/evaluation_results \
  xai-agentic-workflow python run.py query "Your query"
```

### Environment Variables

The Docker container supports all environment variables from the application. Set them via:

1. **`.env` file (recommended):**
```bash
cp .env.example .env
# Edit .env with your values
```

2. **Docker Compose environment section:**
Edit `docker-compose.yml` and add to `environment:` section

3. **Command line:**
```bash
docker run -e GROK_API_KEY=your_key ...
```

**Required variables:**
- `GROK_API_KEY`: Grok API key (required)
- `OPENAI_API_KEY`: OpenAI API key for embeddings (required)

**Optional variables:**
- `GROK_API_BASE_URL`: Default: `https://api.x.ai/v1`
- `GROK_MODEL`: Default: `grok-beta`
- `OPENAI_API_BASE_URL`: Default: `https://api.openai.com/v1`
- `OPENAI_MODEL`: Default: `gpt-4o-mini`
- `CHROMA_DB_PATH`: Default: `/app/data/chroma_db`
- `CHROMA_COLLECTION_NAME`: Default: `x_data`
- `MAX_ITERATIONS`: Default: `10`
- `AGENT_TIMEOUT`: Default: `300`
- `CONTEXT_WINDOW_SIZE`: Default: `10`
- `LOG_LEVEL`: Default: `INFO`

### Data Persistence

The Docker setup uses volumes to persist data:

- **`./data`** → `/app/data`: Contains:
  - `mock_x_data.json`: Generated mock X data
  - `chroma_db/`: Vector store database
  
- **`./evaluation_results`** → `/app/evaluation_results`: Contains:
  - `results.json`: Evaluation results
  - `results.csv`: CSV export
  - Analysis outputs

**Important:** Data in these directories persists between container restarts. To start fresh, delete the directories on the host.

### Container Architecture

The Docker container includes:

- **Base Image:** `python:3.12-slim`
- **Working Directory:** `/app`
- **Entrypoint:** `docker-entrypoint.sh` (handles initialization)
- **Default Command:** `python run.py interactive`

The entrypoint script:
1. Validates required environment variables
2. Creates necessary directories
3. Generates data if missing
4. Sets up vector store if missing
5. Executes the command passed to the container

### Development with Docker

For development, you can mount the source code as a volume:

```yaml
# Add to docker-compose.yml
volumes:
  - ./src:/app/src
  - ./data:/app/data
  - ./evaluation_results:/app/evaluation_results
```

This allows code changes to be reflected without rebuilding (for Python files, not compiled dependencies).

### Production Considerations

For production deployment:

1. **Use specific image tags** instead of `latest`
2. **Set resource limits** in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

3. **Use secrets management** for API keys (Docker secrets, Kubernetes secrets, etc.)
4. **Set up health checks**
5. **Configure logging** to external systems
6. **Use persistent volumes** for production data
7. **Set restart policy:**
```yaml
restart: unless-stopped
```

### Troubleshooting Docker Issues

**Container exits immediately:**
- Check logs: `docker-compose logs agent`
- Verify environment variables are set correctly
- Ensure API keys are valid

**Permission errors:**
- Check volume mount permissions
- On Linux, may need to adjust ownership: `sudo chown -R $USER:$USER ./data`

**Out of memory:**
- Increase Docker memory limit
- Reduce `MAX_ITERATIONS` or `CONTEXT_WINDOW_SIZE`

**Vector store not found:**
- Delete `./data/chroma_db` and let container recreate
- Run: `docker-compose run --rm agent python run.py setup-vector-store`

**Network issues:**
- Ensure Docker has internet access for API calls
- Check firewall settings
- Verify API endpoints are accessible

## Production Deployment

### Environment Variables

Required variables:
- `GROK_API_KEY`: Your Grok API key
- `GROK_API_BASE_URL`: API base URL (default: https://api.x.ai/v1)
- `GROK_MODEL`: Model to use (default: grok-beta)

Optional variables:
- `CHROMA_DB_PATH`: Vector store path
- `MAX_ITERATIONS`: Max agent iterations
- `CONTEXT_WINDOW_SIZE`: Context window size
- `LOG_LEVEL`: Logging level

### Cloud Deployment Options

#### AWS

1. **EC2 Instance**
   - Use Amazon Linux 2 or Ubuntu
   - Install Docker and Docker Compose
   - Set up environment variables
   - Use EBS for persistent storage

2. **ECS (Elastic Container Service)**
   - Build and push image to ECR
   - Create ECS task definition
   - Configure environment variables
   - Use EFS for persistent storage

3. **Lambda** (with modifications)
   - Package as Lambda layer
   - Use serverless framework
   - Note: May need adjustments for Lambda constraints

#### Google Cloud Platform

1. **Compute Engine**
   - Create VM instance
   - Install Docker
   - Deploy using docker-compose

2. **Cloud Run**
   - Build container image
   - Deploy to Cloud Run
   - Configure environment variables
   - Use Cloud Storage for data persistence

#### Azure

1. **Container Instances**
   - Build and push to Azure Container Registry
   - Deploy to Azure Container Instances
   - Configure environment variables

2. **App Service**
   - Use Docker container deployment
   - Configure app settings
   - Use Azure Files for persistence

### Kubernetes Deployment

1. **Create ConfigMap**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: xai-config
data:
  GROK_API_BASE_URL: "https://api.x.ai/v1"
  GROK_MODEL: "grok-beta"
```

2. **Create Secret**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: grok-api-key
type: Opaque
stringData:
  GROK_API_KEY: "your_key_here"
```

3. **Deploy Application**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xai-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: xai-agent
  template:
    metadata:
      labels:
        app: xai-agent
    spec:
      containers:
      - name: agent
        image: xai-agent:latest
        envFrom:
        - configMapRef:
            name: xai-config
        - secretRef:
            name: grok-api-key
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: xai-data-pvc
```

## Monitoring and Logging

### Logging Configuration

Set `LOG_LEVEL` environment variable:
- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages only

### Health Checks

The application can be monitored via:
- Log files (if configured)
- Docker health checks
- Kubernetes liveness/readiness probes

### Metrics Collection

Consider integrating:
- Prometheus for metrics
- Grafana for visualization
- ELK stack for log aggregation

## Scaling Considerations

### Horizontal Scaling

- Stateless agent design allows multiple instances
- Shared vector store (e.g., Pinecone) for consistency
- Load balancer for request distribution

### Vertical Scaling

- Increase `MAX_ITERATIONS` for complex queries
- Larger context windows for more context
- More memory for larger vector stores

### Database Scaling

- Consider Pinecone or Weaviate for production
- Implement caching layer
- Use read replicas for search

## Security Best Practices

1. **API Keys**: Store in secrets management (AWS Secrets Manager, GCP Secret Manager, etc.)
2. **Network**: Use private networks and VPNs
3. **Access Control**: Implement authentication/authorization
4. **Data**: Encrypt data at rest and in transit
5. **Updates**: Keep dependencies updated

## Backup and Recovery

### Data Backup

- Regular backups of vector store
- Backup configuration files
- Version control for code

### Recovery Procedures

1. Restore data from backup
2. Rebuild vector store if needed
3. Verify environment variables
4. Test with sample queries

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

## Performance Tuning

1. **Vector Store**: Optimize chunk size and overlap
2. **Context Window**: Adjust based on query complexity
3. **Retrieval**: Tune semantic/keyword weights
4. **Caching**: Implement result caching for repeated queries
