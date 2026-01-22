"""Command-line interface for interacting with agent."""

import argparse
import logging
import sys
from pathlib import Path

from src.agents.orchestrator import AgentOrchestrator
from src.config.settings import get_settings
from src.data.generator import generate_mock_data
from src.data.loader import load_dataset
from src.evaluation.framework import EvaluationFramework
from src.tools.registry import ToolRegistry
from src.tools.retrieval import HybridRetriever
from src.tools.vector_store import VectorStore, setup_vector_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def setup_agent() -> AgentOrchestrator:
    """Set up agent with all dependencies."""
    logger = logging.getLogger(__name__)

    logger.info("Setting up agent...")

    # Load or generate data
    data_path = Path("data/mock_x_data.json")
    if not data_path.exists():
        logger.info("Data file not found. Generating mock data...")
        generate_mock_data(data_path)

    # Set up vector store
    logger.info("Setting up vector store...")
    vector_store = setup_vector_store(data_path, force_recreate=False)

    # Set up retrieval
    retriever = HybridRetriever(vector_store)

    # Set up tool registry
    tool_registry = ToolRegistry(retriever)

    # Set up agent
    agent = AgentOrchestrator(tool_registry)

    logger.info("Agent setup complete!")
    return agent


def cmd_query(args):
    """Execute a single query."""
    agent = setup_agent()

    print(f"\nQuery: {args.query}")
    print("=" * 60)

    result = agent.run(args.query)

    if result.get("success"):
        print("\nSummary:")
        print("-" * 60)
        print(result.get("summary", "No summary available"))
        print("\n" + "=" * 60)
        print(f"Total time: {result.get('total_time', 0):.2f}s")
    else:
        print(f"\nError: {result.get('error', 'Unknown error')}")
        sys.exit(1)


def cmd_evaluate(args):
    """Run evaluation framework."""
    agent = setup_agent()
    framework = EvaluationFramework(agent)

    output_dir = Path(args.output_dir)
    num_queries = args.num_queries

    print(f"\nRunning evaluation with {num_queries} queries...")
    print("=" * 60)

    metrics = framework.run_evaluation(
        queries=None,  # Use generated queries
        num_queries=num_queries,
        output_dir=output_dir,
    )

    print(f"\nResults saved to {output_dir}/")


def cmd_interactive(args):
    """Interactive mode for querying."""
    agent = setup_agent()

    print("\n" + "=" * 60)
    print("Interactive Agent Mode")
    print("Type 'exit' or 'quit' to exit")
    print("=" * 60 + "\n")

    while True:
        try:
            query = input("Query: ").strip()

            if query.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break

            if not query:
                continue

            print("\nProcessing...")
            result = agent.run(query)

            if result.get("success"):
                print("\n" + "-" * 60)
                print("Summary:")
                print("-" * 60)
                print(result.get("summary", "No summary available"))
                print("-" * 60)
                print(f"Time: {result.get('total_time', 0):.2f}s\n")
            else:
                print(f"\nError: {result.get('error', 'Unknown error')}\n")

            # Reset for next query
            agent.reset()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def cmd_generate_data(args):
    """Generate mock data."""
    output_path = Path(args.output_path)
    print(f"Generating mock data to {output_path}...")
    generate_mock_data(output_path)
    print("Data generation complete!")


def cmd_setup_vector_store(args):
    """Set up vector store."""
    data_path = Path(args.data_path)
    force_recreate = args.force_recreate

    print(f"Setting up vector store from {data_path}...")
    vector_store = setup_vector_store(data_path, force_recreate=force_recreate)
    print(f"Vector store setup complete! Collection size: {vector_store.get_collection_size()}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Multi-Step Agentic Workflow with Grok"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Query command
    query_parser = subparsers.add_parser("query", help="Execute a single query")
    query_parser.add_argument("query", help="Query to execute")
    query_parser.set_defaults(func=cmd_query)

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Run evaluation framework")
    eval_parser.add_argument(
        "--num-queries",
        type=int,
        default=30,
        help="Number of queries to test (default: 30)",
    )
    eval_parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation_results",
        help="Output directory for results (default: evaluation_results)",
    )
    eval_parser.set_defaults(func=cmd_evaluate)

    # Interactive command
    interactive_parser = subparsers.add_parser(
        "interactive", help="Interactive query mode"
    )
    interactive_parser.set_defaults(func=cmd_interactive)

    # Generate data command
    gen_parser = subparsers.add_parser("generate-data", help="Generate mock data")
    gen_parser.add_argument(
        "--output-path",
        type=str,
        default="data/mock_x_data.json",
        help="Output path for generated data (default: data/mock_x_data.json)",
    )
    gen_parser.set_defaults(func=cmd_generate_data)

    # Setup vector store command
    setup_parser = subparsers.add_parser(
        "setup-vector-store", help="Set up vector store"
    )
    setup_parser.add_argument(
        "--data-path",
        type=str,
        default="data/mock_x_data.json",
        help="Path to data file (default: data/mock_x_data.json)",
    )
    setup_parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Force recreation of vector store",
    )
    setup_parser.set_defaults(func=cmd_setup_vector_store)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
