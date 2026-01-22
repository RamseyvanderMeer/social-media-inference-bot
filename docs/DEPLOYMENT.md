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

### Using Docker Compose

1. **Set Environment Variables**
```bash
# Create .env file or set in docker-compose.yml
GROK_API_KEY=your_key_here
```

2. **Build and Run**
```bash
docker-compose build
docker-compose up
```

3. **Access Container**
```bash
docker-compose exec agent bash
```

### Using Dockerfile Directly

1. **Build Image**
```bash
docker build -t xai-agent .
```

2. **Run Container**
```bash
docker run -it \
  -e GROK_API_KEY=your_key_here \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/evaluation_results:/app/evaluation_results \
  xai-agent
```

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
