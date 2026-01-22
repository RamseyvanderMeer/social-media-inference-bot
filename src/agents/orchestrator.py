"""Agent orchestrator core with LlamaIndex and Grok integration."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from llama_index.core.agent import ReActAgent
from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI

from src.agents.context_manager import ContextManager
from src.agents.grok_client import GrokClient, GrokAPIError
from src.config.settings import get_settings
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Main agent orchestrator implementing plan→decompose→execute→refine→summarize loop."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        grok_client: Optional[GrokClient] = None,
        context_manager: Optional[ContextManager] = None,
        settings=None,
    ):
        """Initialize agent orchestrator."""
        if settings is None:
            settings = get_settings()
        self.settings = settings
        self.grok_client = grok_client or GrokClient()
        self.tool_registry = tool_registry
        self.context_manager = context_manager or ContextManager(
            grok_client=self.grok_client
        )

        # Initialize LlamaIndex agent with tools
        tools = self.tool_registry.get_tools()

        # Create LLM for LlamaIndex agent (using OpenAI)
        llm = OpenAI(
            api_key=self.settings.openai.api_key,
            base_url=self.settings.openai.api_base_url,
            model=self.settings.openai.model,
            temperature=self.settings.openai.temperature,
        )

        # Create ReAct agent
        self.agent = ReActAgent(
            tools=tools,
            llm=llm,
            verbose=True,
        )

    def plan(self, query: str) -> str:
        """Generate initial plan using Grok."""
        logger.info(f"Generating plan for query: {query[:50]}...")

        context = self.context_manager.get_context_string()
        available_tools = self.tool_registry.get_tool_names()

        plan = self.grok_client.plan(
            query=query,
            context=context if context.strip() else None,
            available_tools=available_tools,
        )

        self.context_manager.add_step("plan", plan, {"query": query})
        logger.info(f"Plan generated: {plan[:100]}...")

        return plan

    def decompose(self, plan: str) -> List[str]:
        """Decompose plan into sub-tasks."""
        logger.info("Decomposing plan into sub-tasks...")

        # Simple decomposition: split by numbered steps or newlines
        lines = plan.split("\n")
        tasks = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line looks like a task (starts with number, bullet, etc.)
            if any(line.startswith(prefix) for prefix in ["1.", "2.", "3.", "-", "*", "•"]):
                # Remove prefix
                task = line.lstrip("1234567890.-*• ").strip()
                if task:
                    tasks.append(task)
            elif len(line) > 20:  # Consider longer lines as potential tasks
                tasks.append(line)

        if not tasks:
            # Fallback: treat plan as single task
            tasks = [plan]

        logger.info(f"Decomposed into {len(tasks)} sub-tasks")
        return tasks

    def execute(self, query: str, plan: str) -> Dict[str, Any]:
        """Execute plan using LlamaIndex agent."""
        logger.info("Executing plan...")

        start_time = time.time()
        execution_steps = []

        try:
            # Use LlamaIndex agent to execute
            # The agent will use tools based on the query and plan
            full_query = f"Query: {query}\n\nPlan: {plan}\n\nExecute this plan step by step."

            # Create and set event loop BEFORE any agent operations
            # This is critical because agent.run() may need the event loop during initialization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Wrap the async operation
                async def run_agent():
                    # Create context for the agent (inside async context with event loop)
                    ctx = Context(self.agent)
                    # Run the agent and get the handler
                    handler = self.agent.run(full_query, ctx=ctx)
                    # Await the handler to get the response
                    response_obj = await handler
                    return str(response_obj)
                
                # Run the async function with the event loop we created
                response = loop.run_until_complete(run_agent())
            finally:
                # Clean up the event loop
                loop.close()
                asyncio.set_event_loop(None)

            execution_time = time.time() - start_time

            result = {
                "response": response,
                "execution_time": execution_time,
                "steps": execution_steps,
                "success": True,
            }

            self.context_manager.add_step(
                "execution",
                response,
                {"execution_time": execution_time},
            )

            logger.info(f"Execution completed in {execution_time:.2f}s")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Execution error: {e}")

            result = {
                "response": f"Error during execution: {str(e)}",
                "execution_time": execution_time,
                "steps": execution_steps,
                "success": False,
                "error": str(e),
            }

            self.context_manager.add_step(
                "execution_error",
                str(e),
                {"execution_time": execution_time},
            )

            return result

    def refine(self, query: str, execution_result: Dict[str, Any]) -> Optional[str]:
        """Refine approach based on execution results."""
        logger.info("Refining approach...")

        if execution_result.get("success"):
            # Check if results seem complete
            response = execution_result.get("response", "")
            if len(response) < 50:
                logger.info("Response seems incomplete, may need refinement")
                return "Response appears incomplete, consider gathering more information."

        return None

    def summarize(self, query: str, execution_result: Dict[str, Any]) -> str:
        """Generate final summary."""
        logger.info("Generating final summary...")

        response = execution_result.get("response", "")
        context = self.context_manager.get_context_string()

        # Use Grok to create a comprehensive summary
        summary_prompt = f"""Based on the following execution results, create a comprehensive summary that answers the original query.

Original Query: {query}

Execution Results:
{response}

Context:
{context[:1000]}

Provide a clear, well-structured summary that directly addresses the query."""

        messages = [
            {
                "role": "system",
                "content": "You are an expert at creating clear, comprehensive summaries of research results.",
            },
            {"role": "user", "content": summary_prompt},
        ]

        try:
            summary = self.grok_client.chat(messages, temperature=0.3)
            self.context_manager.add_step("summary", summary)
            logger.info("Summary generated")
            return summary
        except GrokAPIError as e:
            logger.error(f"Error generating summary: {e}")
            # Fallback to execution result
            return response

    def run(
        self,
        query: str,
        enable_replanning: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Run complete agent workflow: plan → decompose → execute → refine → summarize.

        Args:
            query: User query
            enable_replanning: Whether to enable replanning (defaults to settings)

        Returns:
            Complete execution result with summary
        """
        logger.info(f"Starting agent workflow for query: {query}")

        start_time = time.time()
        workflow_steps = []

        try:
            # Step 1: Plan
            plan = self.plan(query)
            workflow_steps.append({"step": "plan", "result": plan})

            # Step 2: Decompose
            tasks = self.decompose(plan)
            workflow_steps.append({"step": "decompose", "result": tasks})

            # Step 3: Execute
            execution_result = self.execute(query, plan)
            workflow_steps.append({"step": "execute", "result": execution_result})

            # Step 4: Refine (if needed)
            refinement = self.refine(query, execution_result)
            if refinement:
                workflow_steps.append({"step": "refine", "result": refinement})
                # Could trigger replanning here if needed

            # Step 5: Summarize
            summary = self.summarize(query, execution_result)
            workflow_steps.append({"step": "summary", "result": summary})

            total_time = time.time() - start_time

            result = {
                "query": query,
                "plan": plan,
                "tasks": tasks,
                "execution": execution_result,
                "summary": summary,
                "workflow_steps": workflow_steps,
                "total_time": total_time,
                "success": execution_result.get("success", False),
            }

            logger.info(f"Workflow completed in {total_time:.2f}s")
            return result

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Workflow error: {e}")

            return {
                "query": query,
                "error": str(e),
                "total_time": total_time,
                "success": False,
            }

    def reset(self) -> None:
        """Reset agent state."""
        self.context_manager.clear()
        logger.info("Agent state reset")
