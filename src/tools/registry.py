"""Tool registry for agent tools with LlamaIndex integration."""

import logging
from typing import Any, Dict, List, Optional

from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent

from src.agents.grok_client import GrokClient
from src.tools.retrieval import HybridRetriever

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing and executing agent tools."""

    def __init__(
        self,
        retriever: HybridRetriever,
        grok_client: Optional[GrokClient] = None,
    ):
        """Initialize tool registry."""
        self.retriever = retriever
        self.grok_client = grok_client or GrokClient()
        self.tools: List[FunctionTool] = []
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all available tools."""
        self.tools = [
            self._create_search_tool(),
            self._create_sentiment_analysis_tool(),
            self._create_entity_extraction_tool(),
            self._create_thread_summarization_tool(),
        ]

    def _create_search_tool(self) -> FunctionTool:
        """Create search tool for X data."""

        def search_x_data(
            query: str,
            top_k: int = 5,
        ) -> str:
            """
            Search X (Twitter) data using hybrid retrieval.

            Args:
                query: Search query
                top_k: Number of results to return (default: 5)

            Returns:
                Search results as formatted string
            """
            try:
                results = self.retriever.retrieve(query, top_k=top_k)
                if not results:
                    return "No results found for the query."

                formatted_results = []
                for i, result in enumerate(results, 1):
                    text = result.get("text", "")
                    score = result.get("combined_score", 0.0)
                    formatted_results.append(
                        f"Result {i} (score: {score:.3f}):\n{text}\n"
                    )

                return "\n".join(formatted_results)
            except Exception as e:
                logger.error(f"Search tool error: {e}")
                return f"Error searching data: {str(e)}"

        return FunctionTool.from_defaults(
            fn=search_x_data,
            name="search_x_data",
            description=(
                "Search X (Twitter) data for posts, threads, and discussions. "
                "Use this tool to find relevant information about topics, users, "
                "or discussions. Returns top-k most relevant results."
            ),
        )

    def _create_sentiment_analysis_tool(self) -> FunctionTool:
        """Create sentiment analysis tool."""

        def analyze_sentiment(content: str) -> str:
            """
            Analyze sentiment of text content.

            Args:
                content: Text content to analyze

            Returns:
                Sentiment analysis result
            """
            try:
                if not content or len(content.strip()) == 0:
                    return "Error: Empty content provided."

                result = self.grok_client.analyze(content, analysis_type="sentiment")
                return result
            except Exception as e:
                logger.error(f"Sentiment analysis error: {e}")
                return f"Error analyzing sentiment: {str(e)}"

        return FunctionTool.from_defaults(
            fn=analyze_sentiment,
            name="analyze_sentiment",
            description=(
                "Analyze the sentiment of text content. Identifies if content "
                "is positive, negative, or neutral and explains why. Useful for "
                "understanding the tone of posts or discussions."
            ),
        )

    def _create_entity_extraction_tool(self) -> FunctionTool:
        """Create entity extraction tool."""

        def extract_entities(content: str) -> str:
            """
            Extract key entities from text content.

            Args:
                content: Text content to extract entities from

            Returns:
                List of extracted entities
            """
            try:
                if not content or len(content.strip()) == 0:
                    return "Error: Empty content provided."

                result = self.grok_client.analyze(content, analysis_type="entities")
                return result
            except Exception as e:
                logger.error(f"Entity extraction error: {e}")
                return f"Error extracting entities: {str(e)}"

        return FunctionTool.from_defaults(
            fn=extract_entities,
            name="extract_entities",
            description=(
                "Extract key entities (people, places, organizations, topics) "
                "from text content. Useful for identifying important information "
                "in posts or discussions."
            ),
        )

    def _create_thread_summarization_tool(self) -> FunctionTool:
        """Create thread summarization tool."""

        def summarize_thread(content: str, max_length: int = 500) -> str:
            """
            Summarize thread or long content.

            Args:
                content: Thread or content to summarize
                max_length: Maximum length of summary in characters

            Returns:
                Summary of the content
            """
            try:
                if not content or len(content.strip()) == 0:
                    return "Error: Empty content provided."

                result = self.grok_client.summarize(content, max_length=max_length)
                return result
            except Exception as e:
                logger.error(f"Thread summarization error: {e}")
                return f"Error summarizing thread: {str(e)}"

        return FunctionTool.from_defaults(
            fn=summarize_thread,
            name="summarize_thread",
            description=(
                "Summarize a thread or long piece of content into a concise summary. "
                "Focuses on key points and main ideas. Useful for condensing "
                "long discussions or multiple posts."
            ),
        )

    def get_tools(self) -> List[FunctionTool]:
        """Get all registered tools."""
        return self.tools

    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return [tool.metadata.name for tool in self.tools]

    def get_tool_by_name(self, name: str) -> Optional[FunctionTool]:
        """Get tool by name."""
        for tool in self.tools:
            if tool.metadata.name == name:
                return tool
        return None

    def execute_tool(self, name: str, **kwargs: Any) -> str:
        """Execute a tool by name with given arguments."""
        tool = self.get_tool_by_name(name)
        if tool is None:
            return f"Error: Tool '{name}' not found."

        try:
            result = tool(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Tool execution error for {name}: {e}")
            return f"Error executing tool {name}: {str(e)}"
