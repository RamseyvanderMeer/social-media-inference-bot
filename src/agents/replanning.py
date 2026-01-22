"""Replanning logic with ambiguity detection and confidence scoring."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from src.agents.grok_client import GrokClient
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class ReplanningDetector:
    """Detect ambiguity and trigger replanning."""

    def __init__(
        self,
        grok_client: Optional[GrokClient] = None,
        confidence_threshold: Optional[float] = None,
    ):
        """Initialize replanning detector."""
        settings = get_settings()
        self.grok_client = grok_client or GrokClient()
        self.confidence_threshold = (
            confidence_threshold
            or settings.agent.replanning_confidence_threshold
        )

        # Patterns indicating ambiguity or issues
        self.ambiguity_patterns = [
            r"no results",
            r"not found",
            r"unclear",
            r"ambiguous",
            r"conflicting",
            r"error",
            r"failed",
            r"incomplete",
            r"insufficient",
        ]

    def calculate_confidence(self, result: str, context: Optional[str] = None) -> float:
        """
        Calculate confidence score for execution result.

        Args:
            result: Execution result text
            context: Optional context information

        Returns:
            Confidence score between 0 and 1
        """
        if not result or len(result.strip()) < 10:
            return 0.0

        score = 1.0

        # Check for ambiguity patterns
        result_lower = result.lower()
        for pattern in self.ambiguity_patterns:
            if re.search(pattern, result_lower):
                score -= 0.2

        # Check result length (very short results may be incomplete)
        if len(result) < 50:
            score -= 0.3

        # Check for error indicators
        if "error" in result_lower or "failed" in result_lower:
            score -= 0.4

        # Check for positive indicators
        if any(word in result_lower for word in ["found", "success", "complete", "result"]):
            score += 0.1

        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))

        logger.debug(f"Confidence score: {score:.2f} for result: {result[:50]}...")
        return score

    def detect_ambiguity(
        self,
        result: str,
        query: str,
        context: Optional[str] = None,
    ) -> List[str]:
        """
        Detect ambiguity issues in execution result.

        Args:
            result: Execution result text
            query: Original query
            context: Optional context

        Returns:
            List of identified ambiguity issues
        """
        issues = []

        if not result or len(result.strip()) < 10:
            issues.append("Result is empty or too short")
            return issues

        result_lower = result.lower()

        # Check for no results
        if "no results" in result_lower or "not found" in result_lower:
            issues.append("No results found for the query")

        # Check for conflicting information
        if "conflicting" in result_lower or "contradict" in result_lower:
            issues.append("Conflicting information detected")

        # Check for unclear results
        if "unclear" in result_lower or "ambiguous" in result_lower:
            issues.append("Results are unclear or ambiguous")

        # Check for errors
        if "error" in result_lower:
            issues.append("Errors encountered during execution")

        # Check result completeness
        if len(result) < 100:
            issues.append("Result appears incomplete")

        # Use Grok to analyze if result directly answers query
        try:
            analysis = self._analyze_result_relevance(query, result)
            if "not relevant" in analysis.lower() or "doesn't answer" in analysis.lower():
                issues.append("Result may not directly answer the query")
        except Exception as e:
            logger.warning(f"Could not analyze result relevance: {e}")

        return issues

    def _analyze_result_relevance(self, query: str, result: str) -> str:
        """Use Grok to analyze if result is relevant to query."""
        prompt = f"""Analyze if the following result directly answers the query.

Query: {query}

Result: {result[:500]}

Does this result directly answer the query? Respond with 'Yes' or 'No' and a brief explanation."""

        messages = [
            {
                "role": "system",
                "content": "You are an expert at evaluating if results answer queries.",
            },
            {"role": "user", "content": prompt},
        ]

        return self.grok_client.chat(messages, temperature=0.1, max_tokens=200)

    def should_replan(
        self,
        query: str,
        execution_result: Dict[str, Any],
        original_plan: str,
    ) -> Tuple[bool, List[str]]:
        """
        Determine if replanning is needed.

        Args:
            query: Original query
            execution_result: Result from execution step
            original_plan: Original plan that was executed

        Returns:
            Tuple of (should_replan: bool, issues: List[str])
        """
        if not execution_result.get("success", False):
            return True, ["Execution was not successful"]

        result_text = execution_result.get("response", "")

        # Calculate confidence
        confidence = self.calculate_confidence(result_text)

        # Detect ambiguity issues
        issues = self.detect_ambiguity(result_text, query)

        # Decide if replanning is needed
        should_replan = (
            confidence < self.confidence_threshold
            or len(issues) > 0
            or len(result_text) < 100
        )

        if should_replan:
            logger.info(
                f"Replanning triggered: confidence={confidence:.2f}, "
                f"issues={len(issues)}"
            )

        return should_replan, issues

    def generate_replan(
        self,
        original_query: str,
        original_plan: str,
        execution_result: Dict[str, Any],
        issues: List[str],
    ) -> str:
        """
        Generate revised plan using Grok.

        Args:
            original_query: Original user query
            original_plan: Original plan
            execution_result: Execution result
            issues: List of identified issues

        Returns:
            Revised plan
        """
        logger.info("Generating revised plan...")

        result_text = execution_result.get("response", "")

        revised_plan = self.grok_client.replan(
            original_query=original_query,
            original_plan=original_plan,
            execution_results=result_text,
            ambiguity_issues=issues,
        )

        logger.info("Revised plan generated")
        return revised_plan


class ReplanningManager:
    """Manage replanning process."""

    def __init__(
        self,
        detector: Optional[ReplanningDetector] = None,
        max_replans: int = 2,
    ):
        """Initialize replanning manager."""
        self.detector = detector or ReplanningDetector()
        self.max_replans = max_replans
        self.replan_count = 0

    def check_and_replan(
        self,
        query: str,
        original_plan: str,
        execution_result: Dict[str, Any],
    ) -> Optional[str]:
        """
        Check if replanning is needed and generate revised plan if so.

        Args:
            query: Original query
            original_plan: Original plan
            execution_result: Execution result

        Returns:
            Revised plan if replanning needed, None otherwise
        """
        if self.replan_count >= self.max_replans:
            logger.warning(f"Max replans ({self.max_replans}) reached")
            return None

        should_replan, issues = self.detector.should_replan(
            query, execution_result, original_plan
        )

        if not should_replan:
            return None

        self.replan_count += 1
        logger.info(f"Replanning attempt {self.replan_count}/{self.max_replans}")

        revised_plan = self.detector.generate_replan(
            original_query=query,
            original_plan=original_plan,
            execution_result=execution_result,
            issues=issues,
        )

        return revised_plan

    def reset(self) -> None:
        """Reset replanning counter."""
        self.replan_count = 0
