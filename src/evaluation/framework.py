"""Evaluation framework for testing agent with queries and measuring metrics."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """Calculate and store evaluation metrics."""

    def __init__(self):
        """Initialize metrics."""
        self.results: List[Dict[str, Any]] = []

    def calculate_completion_rate(self) -> float:
        """Calculate completion rate (successful queries / total queries)."""
        if not self.results:
            return 0.0

        successful = sum(1 for r in self.results if r.get("success", False))
        return successful / len(self.results)

    def calculate_step_efficiency(self) -> Dict[str, float]:
        """Calculate step efficiency metrics."""
        if not self.results:
            return {}

        total_steps = []
        total_times = []

        for result in self.results:
            if result.get("success"):
                workflow_steps = result.get("workflow_steps", [])
                total_steps.append(len(workflow_steps))
                total_times.append(result.get("total_time", 0))

        if not total_steps:
            return {}

        return {
            "avg_steps_per_query": sum(total_steps) / len(total_steps),
            "avg_time_per_query": sum(total_times) / len(total_times),
            "min_steps": min(total_steps),
            "max_steps": max(total_steps),
            "min_time": min(total_times),
            "max_time": max(total_times),
        }

    def calculate_summary_quality_scores(self) -> Dict[str, float]:
        """Calculate summary quality metrics (basic heuristics)."""
        if not self.results:
            return {}

        lengths = []
        has_content = 0

        for result in self.results:
            if result.get("success"):
                summary = result.get("summary", "")
                lengths.append(len(summary))
                if len(summary) > 50:
                    has_content += 1

        if not lengths:
            return {}

        return {
            "avg_summary_length": sum(lengths) / len(lengths),
            "completeness_rate": has_content / len(lengths) if lengths else 0.0,
            "min_length": min(lengths),
            "max_length": max(lengths),
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all calculated metrics."""
        return {
            "completion_rate": self.calculate_completion_rate(),
            "step_efficiency": self.calculate_step_efficiency(),
            "summary_quality": self.calculate_summary_quality_scores(),
            "total_queries": len(self.results),
        }

    def add_result(self, result: Dict[str, Any]) -> None:
        """Add evaluation result."""
        self.results.append(result)

    def export_to_json(self, output_path: Path) -> None:
        """Export results to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            "metrics": self.get_all_metrics(),
            "results": self.results,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results exported to {output_path}")

    def export_to_csv(self, output_path: Path) -> None:
        """Export results to CSV file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Flatten results for CSV
        rows = []
        for result in self.results:
            row = {
                "query": result.get("query", ""),
                "success": result.get("success", False),
                "total_time": result.get("total_time", 0),
                "num_steps": len(result.get("workflow_steps", [])),
                "summary_length": len(result.get("summary", "")),
                "error": result.get("error", ""),
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)

        logger.info(f"Results exported to {output_path}")


class QueryGenerator:
    """Generate test queries for evaluation."""

    @staticmethod
    def generate_queries(num_queries: int = 30) -> List[str]:
        """Generate diverse test queries."""
        queries = [
            # Simple fact-finding
            "What are people saying about AI?",
            "Find discussions about Python programming",
            "What topics are trending in tech discussions?",
            "Show me posts about machine learning",
            "What do people think about remote work?",

            # Multi-step reasoning
            "Compare different opinions about AI replacing jobs",
            "What are the main arguments for and against blockchain?",
            "Analyze sentiment of discussions about startups",
            "Find conflicting viewpoints on cloud computing",
            "What are the key themes in data science discussions?",

            # Temporal reasoning
            "What were the main topics discussed last week?",
            "How have opinions about AI changed over time?",
            "Find recent discussions about cybersecurity",

            # Ambiguous/conflicting
            "What do people think about Python vs JavaScript?",
            "Find posts with conflicting opinions about remote work",
            "What are the different perspectives on AI safety?",

            # Entity extraction
            "Who are the main people discussing AI?",
            "What companies are mentioned in tech discussions?",
            "Extract key topics from startup discussions",

            # Sentiment analysis
            "What's the sentiment around machine learning?",
            "How do people feel about cloud computing?",
            "Analyze sentiment of blockchain discussions",

            # Thread analysis
            "Summarize the main points from thread discussions",
            "What are the key arguments in long threads?",
            "Find and summarize evolving discussions",

            # Complex multi-part
            "Find discussions about AI, analyze sentiment, and extract key entities",
            "Compare sentiment of Python vs JavaScript discussions",
            "What are the main topics and their sentiment scores?",
            "Find conflicting information about remote work and summarize both sides",
            "Analyze threads about startups and extract key insights",
        ]

        # Return requested number (repeat if needed)
        if num_queries <= len(queries):
            return queries[:num_queries]

        # Repeat queries if more are needed
        repeated = queries * ((num_queries // len(queries)) + 1)
        return repeated[:num_queries]


class EvaluationFramework:
    """Framework for evaluating agent performance."""

    def __init__(self, agent: AgentOrchestrator):
        """Initialize evaluation framework."""
        self.agent = agent
        self.metrics = EvaluationMetrics()

    def run_evaluation(
        self,
        queries: Optional[List[str]] = None,
        num_queries: int = 30,
        output_dir: Path = Path("evaluation_results"),
    ) -> EvaluationMetrics:
        """
        Run evaluation with test queries.

        Args:
            queries: List of queries to test (if None, generates queries)
            num_queries: Number of queries if generating
            output_dir: Directory for output files

        Returns:
            Evaluation metrics
        """
        if queries is None:
            queries = QueryGenerator.generate_queries(num_queries)

        logger.info(f"Starting evaluation with {len(queries)} queries...")

        output_dir.mkdir(parents=True, exist_ok=True)

        for i, query in enumerate(queries, 1):
            logger.info(f"Evaluating query {i}/{len(queries)}: {query[:50]}...")

            try:
                result = self.agent.run(query)
                self.metrics.add_result(result)

                # Log progress
                if result.get("success"):
                    logger.info(f"Query {i} completed successfully")
                else:
                    logger.warning(f"Query {i} failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error(f"Error evaluating query {i}: {e}")
                self.metrics.add_result({
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "total_time": 0,
                })

            # Reset agent state between queries
            self.agent.reset()

        # Export results
        self.metrics.export_to_json(output_dir / "results.json")
        self.metrics.export_to_csv(output_dir / "results.csv")

        # Print summary
        self._print_summary()

        return self.metrics

    def _print_summary(self) -> None:
        """Print evaluation summary."""
        metrics = self.metrics.get_all_metrics()

        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        print(f"Total Queries: {metrics['total_queries']}")
        print(f"Completion Rate: {metrics['completion_rate']:.2%}")

        if metrics['step_efficiency']:
            eff = metrics['step_efficiency']
            print(f"\nStep Efficiency:")
            print(f"  Average Steps per Query: {eff['avg_steps_per_query']:.2f}")
            print(f"  Average Time per Query: {eff['avg_time_per_query']:.2f}s")
            print(f"  Steps Range: {eff['min_steps']} - {eff['max_steps']}")

        if metrics['summary_quality']:
            qual = metrics['summary_quality']
            print(f"\nSummary Quality:")
            print(f"  Average Length: {qual['avg_summary_length']:.0f} chars")
            print(f"  Completeness Rate: {qual['completeness_rate']:.2%}")
            print(f"  Length Range: {qual['min_length']} - {qual['max_length']}")

        print("=" * 60 + "\n")
