"""Analyze tool effectiveness at retrieving valid information."""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set

def analyze_tool_results(results_file: Path) -> Dict:
    """Analyze tool result quality and effectiveness."""
    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    
    analysis = {
        "total_queries": len(results),
        "tool_result_quality": defaultdict(list),
        "tool_result_stats": defaultdict(lambda: {
            "total_calls": 0,
            "empty_results": 0,
            "error_results": 0,
            "valid_results": 0,
            "avg_result_length": [],
            "result_examples": [],
        }),
        "search_quality": {
            "total_searches": 0,
            "results_with_scores": 0,
            "avg_score": [],
            "low_score_results": 0,  # < 0.3
            "high_score_results": 0,  # > 0.5
        },
        "entity_extraction_quality": {
            "total_calls": 0,
            "results_with_entities": 0,
            "empty_entity_results": 0,
            "entity_count_distribution": [],
        },
        "sentiment_analysis_quality": {
            "total_calls": 0,
            "results_with_sentiment": 0,
            "empty_sentiment_results": 0,
        },
        "summarization_quality": {
            "total_calls": 0,
            "results_with_summary": 0,
            "empty_summary_results": 0,
            "avg_summary_length": [],
        },
        "query_tool_effectiveness": [],
    }

    for i, result in enumerate(results):
        query = result.get("query", f"Query {i+1}")
        execution = result.get("execution", {})
        execution_steps = execution.get("steps", [])
        
        query_analysis = {
            "query": query,
            "tools_used": [],
            "tool_results_quality": {},
        }
        
        for step in execution_steps:
            if not isinstance(step, dict):
                continue
                
            tool_name = step.get("tool_name", "unknown")
            tool_result = step.get("result", "")
            parameters = step.get("parameters", {})
            
            if tool_name == "unknown":
                continue
            
            query_analysis["tools_used"].append(tool_name)
            tool_stats = analysis["tool_result_stats"][tool_name]
            tool_stats["total_calls"] += 1
            
            # Analyze result quality
            result_str = str(tool_result)
            result_length = len(result_str)
            tool_stats["avg_result_length"].append(result_length)
            
            # Check for errors
            is_error = (
                "Error" in result_str or
                "error" in result_str.lower() or
                "No results found" in result_str or
                result_str.strip() == "" or
                len(result_str.strip()) < 10
            )
            
            if is_error:
                if "Error" in result_str or "error" in result_str.lower():
                    tool_stats["error_results"] += 1
                else:
                    tool_stats["empty_results"] += 1
            else:
                tool_stats["valid_results"] += 1
                # Store example (first 3 valid results per tool)
                if len(tool_stats["result_examples"]) < 3:
                    tool_stats["result_examples"].append(result_str[:200])
            
            # Tool-specific analysis
            if tool_name == "search_x_data":
                analysis["search_quality"]["total_searches"] += 1
                
                # Extract search scores
                score_pattern = r"score:\s*([\d.]+)"
                scores = re.findall(score_pattern, result_str)
                if scores:
                    analysis["search_quality"]["results_with_scores"] += 1
                    for score_str in scores:
                        try:
                            score = float(score_str)
                            analysis["search_quality"]["avg_score"].append(score)
                            if score < 0.3:
                                analysis["search_quality"]["low_score_results"] += 1
                            elif score > 0.5:
                                analysis["search_quality"]["high_score_results"] += 1
                        except ValueError:
                            pass
                
                # Check if results contain actual content
                has_content = (
                    "Result" in result_str and
                    len(result_str) > 50 and
                    not is_error
                )
                query_analysis["tool_results_quality"][tool_name] = {
                    "has_content": has_content,
                    "result_length": result_length,
                    "is_error": is_error,
                }
            
            elif tool_name == "extract_entities":
                analysis["entity_extraction_quality"]["total_calls"] += 1
                
                # Check if entities were extracted
                has_entities = (
                    len(result_str) > 20 and
                    not is_error and
                    ("entity" in result_str.lower() or
                     "Entities" in result_str or
                     "People" in result_str or
                     "Organizations" in result_str or
                     "Topics" in result_str or
                     "-" in result_str)  # Bullet points indicate entities
                )
                
                if has_entities:
                    analysis["entity_extraction_quality"]["results_with_entities"] += 1
                    # Count entities (rough estimate by counting bullet points or lines)
                    entity_count = result_str.count("-") + result_str.count("\n")
                    analysis["entity_extraction_quality"]["entity_count_distribution"].append(entity_count)
                else:
                    analysis["entity_extraction_quality"]["empty_entity_results"] += 1
                
                query_analysis["tool_results_quality"][tool_name] = {
                    "has_entities": has_entities,
                    "result_length": result_length,
                    "is_error": is_error,
                }
            
            elif tool_name == "analyze_sentiment":
                analysis["sentiment_analysis_quality"]["total_calls"] += 1
                
                # Check if sentiment was analyzed
                has_sentiment = (
                    len(result_str) > 20 and
                    not is_error and
                    ("sentiment" in result_str.lower() or
                     "positive" in result_str.lower() or
                     "negative" in result_str.lower() or
                     "neutral" in result_str.lower() or
                     "%" in result_str)  # Percentage indicates sentiment scores
                )
                
                if has_sentiment:
                    analysis["sentiment_analysis_quality"]["results_with_sentiment"] += 1
                else:
                    analysis["sentiment_analysis_quality"]["empty_sentiment_results"] += 1
                
                query_analysis["tool_results_quality"][tool_name] = {
                    "has_sentiment": has_sentiment,
                    "result_length": result_length,
                    "is_error": is_error,
                }
            
            elif tool_name == "summarize_thread":
                analysis["summarization_quality"]["total_calls"] += 1
                
                # Check if summary was generated
                has_summary = (
                    len(result_str) > 20 and
                    not is_error
                )
                
                if has_summary:
                    analysis["summarization_quality"]["results_with_summary"] += 1
                    analysis["summarization_quality"]["avg_summary_length"].append(result_length)
                else:
                    analysis["summarization_quality"]["empty_summary_results"] += 1
                
                query_analysis["tool_results_quality"][tool_name] = {
                    "has_summary": has_summary,
                    "result_length": result_length,
                    "is_error": is_error,
                }
        
        analysis["query_tool_effectiveness"].append(query_analysis)
    
    # Calculate averages
    for tool_name, stats in analysis["tool_result_stats"].items():
        if stats["avg_result_length"]:
            stats["avg_result_length"] = sum(stats["avg_result_length"]) / len(stats["avg_result_length"])
        else:
            stats["avg_result_length"] = 0
    
    if analysis["search_quality"]["avg_score"]:
        analysis["search_quality"]["avg_score"] = sum(analysis["search_quality"]["avg_score"]) / len(analysis["search_quality"]["avg_score"])
    else:
        analysis["search_quality"]["avg_score"] = 0
    
    if analysis["summarization_quality"]["avg_summary_length"]:
        analysis["summarization_quality"]["avg_summary_length"] = sum(analysis["summarization_quality"]["avg_summary_length"]) / len(analysis["summarization_quality"]["avg_summary_length"])
    else:
        analysis["summarization_quality"]["avg_summary_length"] = 0
    
    return analysis


def print_effectiveness_analysis(analysis: Dict):
    """Print formatted effectiveness analysis."""
    print("=" * 80)
    print("TOOL RETRIEVAL EFFECTIVENESS ANALYSIS")
    print("=" * 80)
    print()
    
    print(f"Total Queries Analyzed: {analysis['total_queries']}")
    print()
    
    print("-" * 80)
    print("OVERALL TOOL RESULT QUALITY")
    print("-" * 80)
    for tool_name, stats in sorted(analysis["tool_result_stats"].items()):
        if stats["total_calls"] == 0:
            continue
        
        valid_rate = 100 * stats["valid_results"] / stats["total_calls"] if stats["total_calls"] > 0 else 0
        error_rate = 100 * stats["error_results"] / stats["total_calls"] if stats["total_calls"] > 0 else 0
        empty_rate = 100 * stats["empty_results"] / stats["total_calls"] if stats["total_calls"] > 0 else 0
        
        print(f"\n{tool_name}:")
        print(f"  Total Calls: {stats['total_calls']}")
        print(f"  Valid Results: {stats['valid_results']} ({valid_rate:.1f}%)")
        print(f"  Error Results: {stats['error_results']} ({error_rate:.1f}%)")
        print(f"  Empty Results: {stats['empty_results']} ({empty_rate:.1f}%)")
        print(f"  Avg Result Length: {stats['avg_result_length']:.0f} chars")
        
        if stats["result_examples"]:
            print(f"  Example Results:")
            for i, example in enumerate(stats["result_examples"][:2], 1):
                print(f"    {i}. {example[:150]}...")
    
    print()
    print("-" * 80)
    print("SEARCH TOOL (search_x_data) QUALITY")
    print("-" * 80)
    search_qual = analysis["search_quality"]
    print(f"Total Searches: {search_qual['total_searches']}")
    print(f"Searches with Scores: {search_qual['results_with_scores']}")
    if search_qual['avg_score'] > 0:
        print(f"Average Relevance Score: {search_qual['avg_score']:.3f}")
        print(f"Low Score Results (<0.3): {search_qual['low_score_results']}")
        print(f"High Score Results (>0.5): {search_qual['high_score_results']}")
        
        # Calculate score distribution
        if search_qual['results_with_scores'] > 0:
            low_pct = 100 * search_qual['low_score_results'] / search_qual['results_with_scores']
            high_pct = 100 * search_qual['high_score_results'] / search_qual['results_with_scores']
            print(f"Low Score Rate: {low_pct:.1f}%")
            print(f"High Score Rate: {high_pct:.1f}%")
    
    print()
    print("-" * 80)
    print("ENTITY EXTRACTION (extract_entities) QUALITY")
    print("-" * 80)
    entity_qual = analysis["entity_extraction_quality"]
    print(f"Total Calls: {entity_qual['total_calls']}")
    if entity_qual['total_calls'] > 0:
        success_rate = 100 * entity_qual['results_with_entities'] / entity_qual['total_calls']
        print(f"Results with Entities: {entity_qual['results_with_entities']} ({success_rate:.1f}%)")
        print(f"Empty Results: {entity_qual['empty_entity_results']}")
        if entity_qual['entity_count_distribution']:
            avg_entities = sum(entity_qual['entity_count_distribution']) / len(entity_qual['entity_count_distribution'])
            print(f"Average Entities per Result: {avg_entities:.1f}")
    
    print()
    print("-" * 80)
    print("SENTIMENT ANALYSIS (analyze_sentiment) QUALITY")
    print("-" * 80)
    sentiment_qual = analysis["sentiment_analysis_quality"]
    print(f"Total Calls: {sentiment_qual['total_calls']}")
    if sentiment_qual['total_calls'] > 0:
        success_rate = 100 * sentiment_qual['results_with_sentiment'] / sentiment_qual['total_calls']
        print(f"Results with Sentiment: {sentiment_qual['results_with_sentiment']} ({success_rate:.1f}%)")
        print(f"Empty Results: {sentiment_qual['empty_sentiment_results']}")
    
    print()
    print("-" * 80)
    print("SUMMARIZATION (summarize_thread) QUALITY")
    print("-" * 80)
    summary_qual = analysis["summarization_quality"]
    print(f"Total Calls: {summary_qual['total_calls']}")
    if summary_qual['total_calls'] > 0:
        success_rate = 100 * summary_qual['results_with_summary'] / summary_qual['total_calls']
        print(f"Results with Summary: {summary_qual['results_with_summary']} ({success_rate:.1f}%)")
        print(f"Empty Results: {summary_qual['empty_summary_results']}")
        if summary_qual['avg_summary_length'] > 0:
            print(f"Average Summary Length: {summary_qual['avg_summary_length']:.0f} chars")
    
    print()
    print("-" * 80)
    print("KEY FINDINGS")
    print("-" * 80)
    
    # Overall effectiveness
    all_tools_valid = sum(
        stats["valid_results"] for stats in analysis["tool_result_stats"].values()
    )
    all_tools_total = sum(
        stats["total_calls"] for stats in analysis["tool_result_stats"].values()
    )
    
    if all_tools_total > 0:
        overall_valid_rate = 100 * all_tools_valid / all_tools_total
        print(f"1. Overall Tool Success Rate: {overall_valid_rate:.1f}%")
        print(f"   -> {'[OK] Tools are returning valid results' if overall_valid_rate > 80 else '[WARNING] Many tools returning errors or empty results'}")
        print()
    
    # Search quality
    if search_qual['avg_score'] > 0:
        print(f"2. Search Relevance: Average score {search_qual['avg_score']:.3f}")
        if search_qual['avg_score'] > 0.4:
            print(f"   -> [OK] Search results are reasonably relevant")
        elif search_qual['avg_score'] > 0.3:
            print(f"   -> [WARNING] Search results have moderate relevance")
        else:
            print(f"   -> [WARNING] Search results have low relevance")
        print()
    
    # Entity extraction
    if entity_qual['total_calls'] > 0:
        entity_success = 100 * entity_qual['results_with_entities'] / entity_qual['total_calls']
        print(f"3. Entity Extraction Success: {entity_success:.1f}%")
        print(f"   -> {'[OK] Entity extraction is working well' if entity_success > 70 else '[WARNING] Entity extraction may need improvement'}")
        print()
    
    # Sentiment analysis
    if sentiment_qual['total_calls'] > 0:
        sentiment_success = 100 * sentiment_qual['results_with_sentiment'] / sentiment_qual['total_calls']
        print(f"4. Sentiment Analysis Success: {sentiment_success:.1f}%")
        print(f"   -> {'[OK] Sentiment analysis is working well' if sentiment_success > 70 else '[WARNING] Sentiment analysis may need improvement'}")
        print()
    
    # Summarization
    if summary_qual['total_calls'] > 0:
        summary_success = 100 * summary_qual['results_with_summary'] / summary_qual['total_calls']
        print(f"5. Summarization Success: {summary_success:.1f}%")
        print(f"   -> {'[OK] Summarization is working well' if summary_success > 70 else '[WARNING] Summarization may need improvement'}")
        print()
    
    print("=" * 80)


if __name__ == "__main__":
    results_file = Path("evaluation_results/results.json")
    
    if not results_file.exists():
        print(f"Error: {results_file} not found")
        exit(1)
    
    analysis = analyze_tool_results(results_file)
    print_effectiveness_analysis(analysis)
    
    # Save detailed breakdown
    output_file = Path("evaluation_results/tool_effectiveness_analysis.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed analysis saved to: {output_file}")
