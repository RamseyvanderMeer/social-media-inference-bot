"""Hybrid retrieval system combining semantic and keyword search."""

import logging
import re
from collections import Counter
from typing import List, Dict, Tuple

from src.tools.vector_store import VectorStore

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Hybrid retrieval combining semantic and keyword search."""

    def __init__(
        self,
        vector_store: VectorStore,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ):
        """
        Initialize hybrid retriever.

        Args:
            vector_store: Vector store instance for semantic search
            semantic_weight: Weight for semantic search scores (0-1)
            keyword_weight: Weight for keyword search scores (0-1)
        """
        self.vector_store = vector_store
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight

        # Normalize weights
        total_weight = semantic_weight + keyword_weight
        if total_weight > 0:
            self.semantic_weight = semantic_weight / total_weight
            self.keyword_weight = keyword_weight / total_weight

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        # Simple keyword extraction (remove stop words, punctuation)
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "must", "can", "this",
            "that", "these", "those", "what", "which", "who", "when", "where",
            "why", "how",
        }

        # Tokenize and clean
        words = re.findall(r"\b\w+\b", query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords

    def _keyword_search(
        self, query: str, documents: List[Dict], top_k: int = 10
    ) -> List[Tuple[Dict, float]]:
        """Perform keyword-based search using BM25-like scoring."""
        keywords = self._extract_keywords(query)
        if not keywords:
            return []

        # Calculate term frequencies
        keyword_counts = Counter(keywords)

        # Score documents
        scored_docs = []
        for doc in documents:
            text = doc.get("text", "").lower()
            score = 0.0

            for keyword, count in keyword_counts.items():
                # Count occurrences of keyword in document
                occurrences = text.count(keyword)
                if occurrences > 0:
                    # Simple TF scoring (can be enhanced with IDF)
                    score += occurrences * count

            if score > 0:
                scored_docs.append((doc, score))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Normalize scores to 0-1 range
        if scored_docs:
            max_score = scored_docs[0][1]
            if max_score > 0:
                scored_docs = [
                    (doc, score / max_score) for doc, score in scored_docs
                ]

        return scored_docs[:top_k]

    def _semantic_search(
        self, query: str, top_k: int = 10
    ) -> List[Tuple[Dict, float]]:
        """Perform semantic search using vector store."""
        results = self.vector_store.search(query, top_k=top_k * 2)

        # Convert to tuple format with scores
        scored_results = [
            (result, result.get("score", 0.0)) for result in results
        ]

        return scored_results[:top_k]

    def _merge_results(
        self,
        semantic_results: List[Tuple[Dict, float]],
        keyword_results: List[Tuple[Dict, float]],
    ) -> List[Dict]:
        """Merge and deduplicate results from both search methods."""
        # Create a map of document text to combined score
        doc_scores: Dict[str, Dict] = {}

        # Add semantic results
        for doc, score in semantic_results:
            text = doc.get("text", "")
            if text not in doc_scores:
                doc_scores[text] = {
                    "doc": doc,
                    "semantic_score": 0.0,
                    "keyword_score": 0.0,
                    "combined_score": 0.0,
                }
            doc_scores[text]["semantic_score"] = score

        # Add keyword results
        for doc, score in keyword_results:
            text = doc.get("text", "")
            if text not in doc_scores:
                doc_scores[text] = {
                    "doc": doc,
                    "semantic_score": 0.0,
                    "keyword_score": 0.0,
                    "combined_score": 0.0,
                }
            doc_scores[text]["keyword_score"] = score

        # Calculate combined scores
        for text, scores in doc_scores.items():
            combined = (
                scores["semantic_score"] * self.semantic_weight
                + scores["keyword_score"] * self.keyword_weight
            )
            scores["combined_score"] = combined

        # Sort by combined score
        merged = sorted(
            doc_scores.values(),
            key=lambda x: x["combined_score"],
            reverse=True,
        )

        # Return documents with metadata
        results = []
        for item in merged:
            doc = item["doc"].copy()
            doc["semantic_score"] = item["semantic_score"]
            doc["keyword_score"] = item["keyword_score"]
            doc["combined_score"] = item["combined_score"]
            results.append(doc)

        return results

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        semantic_top_k: int = 10,
        keyword_top_k: int = 10,
    ) -> List[Dict]:
        """
        Perform hybrid retrieval combining semantic and keyword search.

        Args:
            query: Search query
            top_k: Number of final results to return
            semantic_top_k: Number of semantic results to consider
            keyword_top_k: Number of keyword results to consider

        Returns:
            List of retrieved documents with scores
        """
        logger.info(f"Hybrid retrieval for query: {query[:50]}...")

        # Perform semantic search
        semantic_results = self._semantic_search(query, top_k=semantic_top_k)
        logger.debug(f"Semantic search returned {len(semantic_results)} results")

        # Perform keyword search (need to get documents first for keyword search)
        # For now, use semantic results as document pool for keyword search
        documents = [doc for doc, _ in semantic_results]
        keyword_results = self._keyword_search(query, documents, top_k=keyword_top_k)
        logger.debug(f"Keyword search returned {len(keyword_results)} results")

        # Merge results
        merged_results = self._merge_results(semantic_results, keyword_results)

        # Return top_k results
        final_results = merged_results[:top_k]

        logger.info(
            f"Hybrid retrieval returned {len(final_results)} results "
            f"(semantic: {len(semantic_results)}, keyword: {len(keyword_results)})"
        )

        return final_results
