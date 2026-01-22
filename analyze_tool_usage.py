"""Analyze tool usage effectiveness from evaluation results."""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set

# Tool names to search for
TOOLS = ["search_x_data", "extract_entities", "analyze_sentiment", "summarize_thread"]


def extract_tools_from_text(text: str) -> Set[str]:
    """Extract tool names mentioned in text."""
    found = set()
    text_lower = text.lower()
    for tool in TOOLS:
        # Look for tool name with various patterns
        patterns = [
            rf"\b{tool}\b",
            rf"`{tool}`",
            rf"{tool}\(",
            rf"{tool}\s*\(",
        ]
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                found.add(tool)
                break
    return found


def analyze_tool_usage(results_file: Path) -> Dict:
    """Analyze tool usage effectiveness."""
    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    
    analysis = {
        "total_queries": len(results),
        "tool_mentions_in_plans": Counter(),
        "tool_mentions_in_execution": Counter(),
        "tool_usage_gap": defaultdict(int),
        "queries_with_tool_plans": 0,
        "queries_with_tool_execution": 0,
        "queries_by_tool_effectiveness": defaultdict(list),
        "execution_steps_tracked": 0,
        "detailed_breakdown": [],
    }

    for i, result in enumerate(results):
        query = result.get("query", f"Query {i+1}")
        plan = result.get("plan", "")
        execution = result.get("execution", {})
        execution_response = execution.get("response", "")
        execution_steps = execution.get("steps", [])
        
        # Track if execution steps are being recorded
        if execution_steps:
            analysis["execution_steps_tracked"] += 1
        
        # Extract tools from plan
        tools_in_plan = extract_tools_from_text(plan)
        
        # Extract tools from execution steps (actual tracked tool calls)
        tools_in_execution = set()
        for step in execution_steps:
            if isinstance(step, dict) and "tool_name" in step:
                tool_name = step.get("tool_name", "")
                if tool_name and tool_name != "unknown":
                    tools_in_execution.add(tool_name)
        
        # Also check execution response text as fallback
        if not tools_in_execution:
            tools_in_execution = extract_tools_from_text(execution_response)
        
        # Count tool mentions
        for tool in tools_in_plan:
            analysis["tool_mentions_in_plans"][tool] += 1
        
        for tool in tools_in_execution:
            analysis["tool_mentions_in_execution"][tool] += 1
        
        # Track queries with tool plans
        if tools_in_plan:
            analysis["queries_with_tool_plans"] += 1
        
        # Track queries with tool execution
        if tools_in_execution:
            analysis["queries_with_tool_execution"] += 1
        
        # Calculate gap (planned but not executed)
        planned_not_executed = tools_in_plan - tools_in_execution
        executed_not_planned = tools_in_execution - tools_in_plan
        
        for tool in planned_not_executed:
            analysis["tool_usage_gap"][tool] += 1
        
        # Categorize effectiveness
        if not tools_in_plan and not tools_in_execution:
            category = "no_tools_needed"
        elif tools_in_plan and not tools_in_execution:
            category = "tools_planned_not_used"
        elif not tools_in_plan and tools_in_execution:
            category = "tools_used_not_planned"
        elif tools_in_plan == tools_in_execution:
            category = "perfect_match"
        elif tools_in_execution.issubset(tools_in_plan):
            category = "partial_usage"
        else:
            category = "mixed_usage"
        
        analysis["queries_by_tool_effectiveness"][category].append(query)
        
        # Detailed breakdown
        analysis["detailed_breakdown"].append({
            "query": query,
            "success": result.get("success", False),
            "tools_planned": sorted(tools_in_plan),
            "tools_executed": sorted(tools_in_execution),
            "planned_not_executed": sorted(planned_not_executed),
            "executed_not_planned": sorted(executed_not_planned),
            "execution_steps_count": len(execution_steps),
            "category": category,
        })
    
    return analysis


def print_analysis(analysis: Dict):
    """Print formatted analysis."""
    print("=" * 80)
    print("TOOL USAGE EFFECTIVENESS ANALYSIS")
    print("=" * 80)
    print()
    
    print(f"Total Queries: {analysis['total_queries']}")
    print(f"Queries with Tool Plans: {analysis['queries_with_tool_plans']} ({100*analysis['queries_with_tool_plans']/analysis['total_queries']:.1f}%)")
    print(f"Queries with Tool Execution: {analysis['queries_with_tool_execution']} ({100*analysis['queries_with_tool_execution']/analysis['total_queries']:.1f}%)")
    print(f"Queries with Execution Steps Tracked: {analysis['execution_steps_tracked']} ({100*analysis['execution_steps_tracked']/analysis['total_queries']:.1f}%)")
    print()
    
    print("-" * 80)
    print("TOOL MENTIONS IN PLANS")
    print("-" * 80)
    total_plan_mentions = sum(analysis['tool_mentions_in_plans'].values())
    for tool, count in analysis['tool_mentions_in_plans'].most_common():
        percentage = 100 * count / analysis['total_queries'] if analysis['total_queries'] > 0 else 0
        print(f"  {tool:25s}: {count:3d} times ({percentage:5.1f}% of queries)")
    print(f"  {'Total':25s}: {total_plan_mentions:3d} mentions")
    print()
    
    print("-" * 80)
    print("TOOL MENTIONS IN EXECUTION (indicating actual usage)")
    print("-" * 80)
    total_exec_mentions = sum(analysis['tool_mentions_in_execution'].values())
    for tool, count in analysis['tool_mentions_in_execution'].most_common():
        percentage = 100 * count / analysis['total_queries'] if analysis['total_queries'] > 0 else 0
        print(f"  {tool:25s}: {count:3d} times ({percentage:5.1f}% of queries)")
    print(f"  {'Total':25s}: {total_exec_mentions:3d} mentions")
    print()
    
    print("-" * 80)
    print("TOOL USAGE GAP (Planned but Not Executed)")
    print("-" * 80)
    if analysis['tool_usage_gap']:
        for tool, count in sorted(analysis['tool_usage_gap'].items(), key=lambda x: -x[1]):
            percentage = 100 * count / analysis['total_queries'] if analysis['total_queries'] > 0 else 0
            print(f"  {tool:25s}: {count:3d} queries ({percentage:5.1f}%)")
    else:
        print("  No significant gaps found")
    print()
    
    print("-" * 80)
    print("QUERY EFFECTIVENESS CATEGORIES")
    print("-" * 80)
    for category, queries in sorted(analysis['queries_by_tool_effectiveness'].items()):
        count = len(queries)
        percentage = 100 * count / analysis['total_queries'] if analysis['total_queries'] > 0 else 0
        print(f"  {category:30s}: {count:3d} queries ({percentage:5.1f}%)")
        if count <= 5 and count > 0:
            for q in queries[:3]:
                print(f"    - {q[:70]}")
    print()
    
    print("-" * 80)
    print("KEY FINDINGS")
    print("-" * 80)
    
    # Calculate effectiveness metrics
    perfect_match = len(analysis['queries_by_tool_effectiveness']['perfect_match'])
    partial_usage = len(analysis['queries_by_tool_effectiveness']['partial_usage'])
    tools_planned_not_used = len(analysis['queries_by_tool_effectiveness']['tools_planned_not_used'])
    
    effectiveness_rate = 100 * (perfect_match + partial_usage) / analysis['total_queries'] if analysis['total_queries'] > 0 else 0
    tool_usage_rate = 100 * analysis['queries_with_tool_execution'] / analysis['queries_with_tool_plans'] if analysis['queries_with_tool_plans'] > 0 else 0
    
    print(f"1. Tool Execution Tracking: {analysis['execution_steps_tracked']}/{analysis['total_queries']} queries have execution steps tracked")
    print(f"   -> {'[CRITICAL] Execution steps are NOT being tracked!' if analysis['execution_steps_tracked'] == 0 else '[OK] Execution steps are being tracked'}")
    print()
    
    print(f"2. Tool Usage Rate: {tool_usage_rate:.1f}% of queries with tool plans actually used tools")
    print(f"   -> {'[WARNING] Many tools planned but not executed' if tool_usage_rate < 50 else '[OK] Most planned tools are being used'}")
    print()
    
    print(f"3. Effectiveness Rate: {effectiveness_rate:.1f}% of queries have perfect or partial tool usage")
    print(f"   -> {'[WARNING] Low tool effectiveness' if effectiveness_rate < 50 else '[OK] Good tool effectiveness'}")
    print()
    
    print(f"4. Tools Planned but Not Used: {tools_planned_not_used} queries")
    print(f"   -> {'[WARNING] Significant gap between planning and execution' if tools_planned_not_used > analysis['total_queries'] * 0.3 else '[OK] Good alignment between planning and execution'}")
    print()
    
    print("=" * 80)


if __name__ == "__main__":
    results_file = Path("evaluation_results/results.json")
    
    if not results_file.exists():
        print(f"Error: {results_file} not found")
        exit(1)
    
    analysis = analyze_tool_usage(results_file)
    print_analysis(analysis)
    
    # Save detailed breakdown
    output_file = Path("evaluation_results/tool_usage_analysis.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed analysis saved to: {output_file}")
