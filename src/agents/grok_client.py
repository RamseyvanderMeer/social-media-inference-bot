"""Grok API client with retry logic and error handling."""

import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class GrokAPIError(Exception):
    """Base exception for Grok API errors."""

    pass


class GrokRateLimitError(GrokAPIError):
    """Exception for rate limit errors."""

    pass


class GrokClient:
    """Client for interacting with Grok API."""

    def __init__(self, settings=None):
        """Initialize Grok client with settings."""
        if settings is None:
            settings = get_settings()
        self.settings = settings.grok
        self.client = OpenAI(
            api_key=self.settings.api_key,
            base_url=self.settings.api_base_url,
            timeout=self.settings.timeout,
        )

    @retry(
        retry=retry_if_exception_type((GrokRateLimitError, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Send chat completion request to Grok API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters for API call

        Returns:
            Response content as string

        Raises:
            GrokAPIError: For API errors
            GrokRateLimitError: For rate limit errors
        """
        try:
            response = self.client.chat.completions.create(
                model=self.settings.model,
                messages=messages,
                temperature=temperature or self.settings.temperature,
                max_tokens=max_tokens or self.settings.max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                logger.warning(f"Rate limit hit: {e}")
                raise GrokRateLimitError(f"Rate limit exceeded: {e}") from e
            logger.error(f"Grok API error: {e}")
            raise GrokAPIError(f"API call failed: {e}") from e

    def plan(
        self,
        query: str,
        context: Optional[str] = None,
        available_tools: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a plan for answering the query.

        Args:
            query: User query to plan for
            context: Optional context from previous steps
            available_tools: List of available tool names

        Returns:
            Plan as string
        """
        system_prompt = """You are an expert planning assistant. Your task is to create a detailed, step-by-step plan for answering a research query using available tools.

Available tools: {tools}

Your plan should:
1. Break down the query into clear, actionable sub-tasks
2. Specify which tools to use for each sub-task
3. Identify dependencies between sub-tasks
4. Consider potential ambiguities or edge cases

Format your response as a clear, numbered list of steps."""

        tools_str = ", ".join(available_tools) if available_tools else "search_x_data, analyze_sentiment, extract_entities, summarize_thread"

        messages = [
            {
                "role": "system",
                "content": system_prompt.format(tools=tools_str),
            },
            {
                "role": "user",
                "content": f"Query: {query}\n\n{('Context: ' + context) if context else ''}\n\nCreate a plan to answer this query.",
            },
        ]

        return self.chat(messages, temperature=0.3)

    def replan(
        self,
        original_query: str,
        original_plan: str,
        execution_results: str,
        ambiguity_issues: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a revised plan based on execution results and ambiguity issues.

        Args:
            original_query: Original user query
            original_plan: The plan that was executed
            execution_results: Results from plan execution
            ambiguity_issues: List of identified ambiguity issues

        Returns:
            Revised plan as string
        """
        system_prompt = """You are an expert planning assistant. The previous plan encountered issues or ambiguities. Your task is to create a revised plan that addresses these problems.

The revised plan should:
1. Address the identified ambiguities or issues
2. Use different tools or approaches if needed
3. Be more specific about what to search for or analyze
4. Consider alternative interpretations of the query

Format your response as a clear, numbered list of steps."""

        issues_str = (
            "\n".join(f"- {issue}" for issue in ambiguity_issues)
            if ambiguity_issues
            else "No specific issues identified, but results were ambiguous or incomplete."
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"""Original Query: {original_query}

Original Plan:
{original_plan}

Execution Results:
{execution_results}

Identified Issues:
{issues_str}

Create a revised plan that addresses these issues.""",
            },
        ]

        return self.chat(messages, temperature=0.3)

    def analyze(
        self,
        content: str,
        analysis_type: str = "general",
    ) -> str:
        """
        Analyze content using Grok.

        Args:
            content: Content to analyze
            analysis_type: Type of analysis (sentiment, entities, summary, general)

        Returns:
            Analysis result as string
        """
        analysis_prompts = {
            "sentiment": "Analyze the sentiment of the following content. Identify if it's positive, negative, or neutral, and explain why.",
            "entities": "Extract key entities (people, places, organizations, topics) from the following content. List them clearly.",
            "summary": "Provide a concise summary of the following content, highlighting the main points.",
            "general": "Analyze the following content and provide insights about its key themes, arguments, and implications.",
        }

        prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ]

        return self.chat(messages)

    def summarize(
        self,
        content: str,
        max_length: int = 500,
    ) -> str:
        """
        Summarize content using Grok.

        Args:
            content: Content to summarize
            max_length: Maximum length of summary in characters

        Returns:
            Summary as string
        """
        messages = [
            {
                "role": "system",
                "content": f"Provide a concise summary in approximately {max_length} characters. Focus on key points and main ideas.",
            },
            {"role": "user", "content": content},
        ]

        return self.chat(messages, temperature=0.5)
