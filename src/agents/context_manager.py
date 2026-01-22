"""Context manager for conversation and execution context."""

import logging
from collections import deque
from typing import Any, Dict, List, Optional

from src.agents.grok_client import GrokClient
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class ContextStep:
    """Represents a single step in the execution context."""

    def __init__(
        self,
        step_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize context step."""
        self.step_type = step_type  # 'plan', 'tool_call', 'result', 'refinement', etc.
        self.content = content
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "step_type": self.step_type,
            "content": self.content,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"[{self.step_type}] {self.content[:100]}..."


class ContextManager:
    """Manage conversation and execution context with sliding window."""

    def __init__(
        self,
        window_size: Optional[int] = None,
        enable_compression: bool = True,
        grok_client: Optional[GrokClient] = None,
    ):
        """Initialize context manager."""
        settings = get_settings()
        self.window_size = window_size or settings.agent.context_window_size
        self.enable_compression = enable_compression
        self.grok_client = grok_client or GrokClient()

        # Use deque for efficient sliding window
        self.steps: deque[ContextStep] = deque(maxlen=self.window_size)
        self.compressed_history: List[str] = []

    def add_step(
        self,
        step_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a step to the context."""
        step = ContextStep(step_type, content, metadata)
        self.steps.append(step)
        logger.debug(f"Added context step: {step}")

    def get_recent_steps(self, n: Optional[int] = None) -> List[ContextStep]:
        """Get recent N steps."""
        if n is None:
            return list(self.steps)
        return list(self.steps)[-n:]

    def get_context_string(self, include_compressed: bool = True) -> str:
        """Get context as formatted string."""
        parts = []

        # Add compressed history if enabled
        if include_compressed and self.compressed_history:
            parts.append("=== Compressed History ===")
            parts.extend(self.compressed_history)
            parts.append("")

        # Add recent steps
        parts.append("=== Recent Steps ===")
        for step in self.steps:
            parts.append(f"[{step.step_type.upper()}] {step.content}")

        return "\n".join(parts)

    def compress_context(self, force: bool = False) -> None:
        """Compress old context using summarization."""
        if not self.enable_compression:
            return

        # Only compress if we have enough steps or if forced
        if not force and len(self.steps) < self.window_size:
            return

        # Get steps to compress (all but the most recent few)
        steps_to_compress = list(self.steps)[:-3]  # Keep last 3 steps uncompressed

        if not steps_to_compress:
            return

        logger.info(f"Compressing {len(steps_to_compress)} context steps...")

        # Create summary of steps to compress
        compressed_content = "\n".join(
            f"[{step.step_type}] {step.content[:200]}"
            for step in steps_to_compress
        )

        # Use Grok to summarize
        try:
            summary = self.grok_client.summarize(
                compressed_content, max_length=500
            )
            self.compressed_history.append(summary)

            # Remove compressed steps (keep only recent ones)
            # Since we're using deque with maxlen, we just need to track what we compressed
            # In practice, we'd remove the old steps, but deque handles this automatically

            logger.info("Context compression completed")
        except Exception as e:
            logger.error(f"Error compressing context: {e}")
            # Fallback: just add a simple summary
            self.compressed_history.append(
                f"Previous {len(steps_to_compress)} steps: {compressed_content[:200]}..."
            )

    def clear(self) -> None:
        """Clear all context."""
        self.steps.clear()
        self.compressed_history.clear()
        logger.info("Context cleared")

    def get_full_history(self) -> Dict[str, Any]:
        """Get full context history as dictionary."""
        return {
            "compressed_history": self.compressed_history,
            "recent_steps": [step.to_dict() for step in self.steps],
            "total_steps": len(self.steps) + len(self.compressed_history),
        }

    def prune(self, keep_last_n: int = 5) -> None:
        """Prune context, keeping only last N steps."""
        if len(self.steps) <= keep_last_n:
            return

        # Compress everything except last N steps
        steps_to_compress = list(self.steps)[:-keep_last_n]
        if steps_to_compress:
            self.compress_context(force=True)
            # Remove old steps (deque will handle this with maxlen, but we can be explicit)
            for _ in range(len(self.steps) - keep_last_n):
                if self.steps:
                    self.steps.popleft()

        logger.info(f"Pruned context, keeping last {keep_last_n} steps")
