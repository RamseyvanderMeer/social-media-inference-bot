# Troubleshooting Guide

## Common Issues and Solutions

### API Key Issues

**Problem**: `ValueError: GROK_API_KEY must be set`

**Solution**:
1. Check that `.env` file exists and contains `GROK_API_KEY`
2. Verify the API key is correct and has proper permissions
3. Ensure environment variables are loaded (check with `printenv GROK_API_KEY`)

**Problem**: `GrokAPIError: API call failed`

**Solution**:
1. Verify API key is valid and not expired
2. Check API base URL is correct
3. Verify network connectivity
4. Check rate limits haven't been exceeded

### Vector Store Issues

**Problem**: `FileNotFoundError: Data file not found`

**Solution**:
```bash
# Generate mock data
python run.py generate-data
```

**Problem**: Vector store not finding results

**Solution**:
1. Rebuild vector store:
```bash
python run.py setup-vector-store --force-recreate
```
2. Verify data was indexed correctly
3. Check ChromaDB path is accessible

**Problem**: ChromaDB connection errors

**Solution**:
1. Check `CHROMA_DB_PATH` is set correctly
2. Ensure directory has write permissions
3. Try deleting and recreating the database

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
1. Ensure you're in the project root directory
2. Activate virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Check Python path includes project root

**Problem**: `ImportError: cannot import name 'X' from 'Y'`

**Solution**:
1. Verify all dependencies are installed
2. Check for circular imports
3. Ensure Python version is 3.12+

### Agent Execution Issues

**Problem**: Agent times out or exceeds max iterations

**Solution**:
1. Increase `MAX_ITERATIONS` in `.env`
2. Increase `AGENT_TIMEOUT` in `.env`
3. Simplify query or break into smaller parts
4. Check if tools are responding correctly

**Problem**: Agent returns empty or incomplete results

**Solution**:
1. Check if data exists in vector store
2. Verify retrieval is working: test with simple query
3. Check Grok API is responding
4. Review logs for errors

**Problem**: Replanning triggered too frequently

**Solution**:
1. Adjust `replanning_confidence_threshold` in settings
2. Improve data quality or query specificity
3. Review ambiguity detection patterns

### Docker Issues

**Problem**: Container fails to start

**Solution**:
1. Check Docker logs: `docker-compose logs`
2. Verify environment variables are set
3. Ensure Docker has sufficient resources
4. Check Dockerfile syntax

**Problem**: Volume mounting issues

**Solution**:
1. Verify volume paths in `docker-compose.yml`
2. Check file permissions on host
3. Ensure directories exist on host

**Problem**: Network connectivity in container

**Solution**:
1. Check DNS settings
2. Verify firewall rules
3. Test API connectivity from container

### Performance Issues

**Problem**: Slow query execution

**Solution**:
1. Check vector store size (may need optimization)
2. Reduce `CONTEXT_WINDOW_SIZE` if too large
3. Enable context compression
4. Consider caching frequently used results
5. Check network latency to Grok API

**Problem**: High memory usage

**Solution**:
1. Reduce context window size
2. Enable context compression
3. Limit number of retrieved documents
4. Use smaller embedding models

**Problem**: Vector store too large

**Solution**:
1. Reduce dataset size
2. Optimize chunk size
3. Consider using cloud vector store (Pinecone)
4. Implement data pruning

### Evaluation Issues

**Problem**: Evaluation fails or hangs

**Solution**:
1. Reduce number of queries for testing
2. Check API rate limits
3. Verify data is loaded correctly
4. Check output directory permissions

**Problem**: Metrics seem incorrect

**Solution**:
1. Review metric calculation logic
2. Check if queries are appropriate
3. Verify evaluation results in JSON/CSV
4. Compare with manual evaluation

### Configuration Issues

**Problem**: Settings not loading correctly

**Solution**:
1. Verify `.env` file format (no spaces around `=`)
2. Check environment variable names match exactly
3. Restart application after changing `.env`
4. Use `get_settings()` to verify loaded values

**Problem**: Default values not working

**Solution**:
1. Check Pydantic field defaults
2. Verify environment variable parsing
3. Review settings.py for correct defaults

## Debugging Tips

### Enable Debug Logging

Set in `.env`:
```
LOG_LEVEL=DEBUG
```

### Check Component Status

```python
from src.config.settings import get_settings
settings = get_settings()
print(settings.grok.api_key[:10] + "...")  # Don't print full key
```

### Test Individual Components

```python
# Test Grok client
from src.agents.grok_client import GrokClient
client = GrokClient()
result = client.chat([{"role": "user", "content": "Hello"}])
print(result)

# Test vector store
from src.tools.vector_store import VectorStore
vs = VectorStore()
results = vs.search("test query", top_k=5)
print(results)

# Test retrieval
from src.tools.retrieval import HybridRetriever
retriever = HybridRetriever(vs)
results = retriever.retrieve("test query")
print(results)
```

### Verify Data

```python
from src.data.loader import load_dataset
dataset = load_dataset()
print(f"Loaded {len(dataset.posts)} posts")
print(f"Metadata: {dataset.metadata}")
```

## Getting Help

1. Check logs for detailed error messages
2. Review relevant documentation
3. Verify all prerequisites are met
4. Test with minimal configuration
5. Check GitHub issues (if applicable)

## Log Locations

- Application logs: Console output (or configured log file)
- Docker logs: `docker-compose logs agent`
- System logs: `/var/log/` (Linux) or system event viewer (Windows)

## Known Limitations

1. **Rate Limits**: Grok API has rate limits; implement backoff
2. **Context Size**: Large contexts may exceed token limits
3. **Vector Store**: ChromaDB may be slow with very large datasets
4. **Replanning**: May add latency but improves accuracy
5. **Mock Data**: Generated data may not reflect real-world patterns

## Performance Benchmarks

Typical performance (on local machine):
- Simple query: 5-10 seconds
- Complex query: 15-30 seconds
- Evaluation (30 queries): 10-15 minutes

These may vary based on:
- API response times
- Vector store size
- Network latency
- System resources
