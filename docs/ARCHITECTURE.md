# Architecture Documentation

## System Overview

The Autonomous Multi-Step Agentic Workflow system is designed as a modular, chunk-based architecture that enables autonomous research and analysis on X (Twitter) data using Grok as the central reasoning engine.

## Core Components

### 1. Data Layer

**Purpose**: Generate and manage mock X data for testing and development.

**Components**:
- `data/generator.py`: Generates realistic mock X posts with ambiguity scenarios
- `data/loader.py`: Loads and parses dataset into structured format
- `data/models.py`: Pydantic models for data structures (Post, Thread, User, Dataset)

**Key Features**:
- Simulates posts, threads, and user interactions
- Includes ambiguity scenarios (sarcasm, evolving threads, conflicting information)
- Exports to JSON format for easy loading

### 2. Vector Store

**Purpose**: Semantic search and retrieval using embeddings.

**Components**:
- `tools/vector_store.py`: ChromaDB integration with LlamaIndex
- Uses OpenAI embeddings for document encoding
- Implements document chunking for efficient indexing

**Design Decisions**:
- **ChromaDB**: Chosen for local development and easy setup
- **LlamaIndex**: Provides abstraction layer for vector operations
- **Chunking**: 512 tokens with 50 token overlap for optimal retrieval

### 3. Retrieval System

**Purpose**: Hybrid search combining semantic and keyword approaches.

**Components**:
- `tools/retrieval.py`: HybridRetriever class
- Semantic search via vector store
- Keyword search using BM25-like scoring
- Weighted combination of both approaches

**Design Decisions**:
- **Hybrid Approach**: Combines strengths of semantic and keyword search
- **Default Weights**: 70% semantic, 30% keyword (configurable)
- **Deduplication**: Merges results from both methods

### 4. Tool Registry

**Purpose**: Manage and execute agent tools.

**Components**:
- `tools/registry.py`: ToolRegistry class
- Integrates with LlamaIndex FunctionTool system
- Available tools:
  - `search_x_data`: Hybrid retrieval
  - `analyze_sentiment`: Sentiment analysis via Grok
  - `extract_entities`: Entity extraction via Grok
  - `summarize_thread`: Thread summarization via Grok

**Design Decisions**:
- **LlamaIndex Integration**: Uses FunctionTool for seamless agent integration
- **Grok for Analysis**: Leverages Grok's reasoning for complex analysis tasks
- **Error Handling**: Graceful degradation on tool failures

### 5. Agent Orchestrator

**Purpose**: Main agent loop coordinating all components.

**Components**:
- `agents/orchestrator.py`: AgentOrchestrator class
- Workflow steps: Plan → Decompose → Execute → Refine → Summarize
- LlamaIndex ReAct agent for tool execution
- Grok integration for planning and summarization

**Design Decisions**:
- **LlamaIndex ReAct**: Uses proven ReAct pattern for tool use
- **Grok for Planning**: Leverages Grok's planning capabilities
- **Modular Steps**: Each step can be customized or extended

### 6. Context Manager

**Purpose**: Manage conversation and execution context efficiently.

**Components**:
- `agents/context_manager.py`: ContextManager class
- Sliding window for recent steps
- Context compression via summarization
- Configurable window size

**Design Decisions**:
- **Sliding Window**: Keeps recent context while managing token limits
- **Compression**: Uses Grok to summarize old context
- **Flexible Size**: Configurable based on use case

### 7. Replanning System

**Purpose**: Detect ambiguity and trigger replanning.

**Components**:
- `agents/replanning.py`: ReplanningDetector and ReplanningManager
- Confidence scoring mechanism
- Ambiguity detection patterns
- Automatic replanning trigger

**Design Decisions**:
- **Confidence Threshold**: Configurable threshold for replanning
- **Pattern-Based Detection**: Identifies common ambiguity indicators
- **Grok-Powered Replanning**: Uses Grok to generate revised plans

## Data Flow

```
User Query
    ↓
Agent Orchestrator
    ↓
Grok Planning
    ↓
Task Decomposition
    ↓
Tool Selection (LlamaIndex ReAct)
    ↓
Tool Execution
    ├──→ Hybrid Retrieval
    ├──→ Sentiment Analysis
    ├──→ Entity Extraction
    └──→ Summarization
    ↓
Result Collection
    ↓
Refinement (if needed)
    ↓
Replanning (if ambiguous)
    ↓
Grok Summarization
    ↓
Final Result
```

## Integration Points

### Grok Integration
- **Planning**: Initial plan generation
- **Replanning**: Revised plan when ambiguity detected
- **Analysis**: Sentiment, entities, summarization
- **Final Summary**: Comprehensive result summarization

### LlamaIndex Integration
- **Agent Framework**: ReAct agent for tool orchestration
- **Vector Store**: ChromaDB integration
- **Tools**: FunctionTool system for tool registration

### ChromaDB Integration
- **Storage**: Persistent vector database
- **Search**: Semantic similarity search
- **Indexing**: Document chunking and embedding

## Configuration Management

All configuration is centralized in `config/settings.py`:

- **GrokSettings**: API configuration
- **VectorStoreSettings**: Database and embedding settings
- **AgentSettings**: Agent loop parameters
- **LoggingSettings**: Logging configuration

Uses Pydantic for validation and environment variable loading.

## Error Handling

- **API Errors**: Retry logic with exponential backoff
- **Tool Failures**: Graceful degradation with error messages
- **Context Issues**: Automatic compression and pruning
- **Replanning**: Automatic trigger on low confidence

## Performance Considerations

- **Vector Store**: Persistent storage for fast retrieval
- **Context Compression**: Reduces token usage
- **Caching**: Vector store caching for repeated queries
- **Parallel Execution**: Potential for parallel tool execution (future)

## Extensibility

The system is designed for easy extension:

- **New Tools**: Add to ToolRegistry
- **New Data Sources**: Implement data loader interface
- **Custom Agents**: Extend AgentOrchestrator
- **Alternative LLMs**: Swap Grok client implementation

## Trade-offs

1. **Local vs Cloud Vector Store**: ChromaDB chosen for simplicity, but can swap to Pinecone for scale
2. **Hybrid Retrieval**: More complex but better results than semantic-only
3. **Context Compression**: Saves tokens but may lose nuance
4. **Replanning**: Adds latency but improves accuracy

## Future Enhancements

- Parallel tool execution
- Multi-modal support
- Advanced caching strategies
- Real-time data streaming
- Multi-agent collaboration
