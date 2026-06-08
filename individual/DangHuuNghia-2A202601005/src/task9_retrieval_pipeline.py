"""
Task 9 - Complete retrieval pipeline.

Pipeline:
    1. Semantic search over Task 4 vectors
    2. Lexical BM25 search over the same chunks
    3. Merge dense + sparse results with RRF
    4. Rerank merged candidates
    5. Fallback to PageIndex when hybrid confidence is too low
"""

from __future__ import annotations

import sys
from pathlib import Path


try:
    from src.task5_semantic_search import semantic_search
    from src.task6_lexical_search import lexical_search
    from src.task7_reranking import rerank, rerank_rrf
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.task5_semantic_search import semantic_search
    from src.task6_lexical_search import lexical_search
    from src.task7_reranking import rerank, rerank_rrf

try:
    from src.task8_pageindex_vectorless import pageindex_search
except Exception:
    pageindex_search = None


SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5
RERANK_METHOD = "cross_encoder"


def with_source(results: list[dict], source: str) -> list[dict]:
    normalized: list[dict] = []
    for result in results:
        item = result.copy()
        item["metadata"] = dict(result.get("metadata", {}))
        item["source"] = source
        normalized.append(item)
    return normalized


def normalize_scores(results: list[dict]) -> list[dict]:
    if not results:
        return results

    scores = [float(item.get("score", 0.0)) for item in results]
    low = min(scores)
    high = max(scores)

    normalized: list[dict] = []
    for item, score in zip(results, scores):
        new_item = item.copy()
        if high == low:
            new_score = 1.0 if high > 0 else 0.0
        else:
            new_score = (score - low) / (high - low)
        new_item["score"] = float(new_score)
        normalized.append(new_item)
    return normalized


def safe_pageindex_search(query: str, top_k: int) -> list[dict]:
    if pageindex_search is None:
        return []

    try:
        fallback = pageindex_search(query, top_k=top_k)
    except Exception:
        return []

    fallback = with_source(fallback[:top_k], "pageindex")
    fallback.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    return fallback


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieve relevant chunks with hybrid search and fallback.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict, 'source': str}
        where source is either 'hybrid' or 'pageindex'.
    """
    if top_k <= 0:
        return []

    query = query.strip()
    if not query:
        return []

    candidate_k = max(top_k * 3, 10)

    dense_results = semantic_search(query, top_k=candidate_k)
    sparse_results = lexical_search(query, top_k=candidate_k)

    merged = rerank_rrf([dense_results, sparse_results], top_k=candidate_k)
    merged = with_source(merged, "hybrid")

    if use_reranking and merged:
        final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
        final_results = with_source(final_results, "hybrid")
    else:
        final_results = merged[:top_k]

    best_score = final_results[0]["score"] if final_results else 0.0

    if best_score < score_threshold:
        fallback = safe_pageindex_search(query, top_k)
        if fallback:
            return fallback[:top_k]
        return []

    return normalize_scores(final_results[:top_k])


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma túy",
        "Nghệ sĩ nào bị bắt vì sử dụng ma túy năm 2024",
        "Luật phòng chống ma túy 2021 quy định gì về cai nghiện",
    ]

    for query in test_queries:
        sys.stdout.buffer.write(f"\nQuery: {query}\n".encode("utf-8"))
        sys.stdout.buffer.write(("-" * 60 + "\n").encode("utf-8"))
        for index, result in enumerate(retrieve(query, top_k=3), 1):
            preview = result["content"].replace("\n", " ")[:100]
            line = f"{index}. [{result['score']:.3f}] [{result['source']}] {preview}...\n"
            sys.stdout.buffer.write(line.encode("utf-8", errors="replace"))
