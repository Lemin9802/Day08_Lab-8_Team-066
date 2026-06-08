"""
Task 9: complete retrieval pipeline.

Pipeline:
1. Run semantic search and lexical BM25 search.
2. Merge result lists with Reciprocal Rank Fusion.
3. Rerank merged candidates.
4. Fall back to Task 8 PageIndex-style vectorless retrieval if hybrid quality is
   below threshold.
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search

SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5
RERANK_METHOD = "cross_encoder"


def _with_source(results: list[dict], source: str) -> list[dict]:
    enriched = []
    for result in results:
        item = dict(result)
        item["source"] = source
        enriched.append(item)
    return enriched


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieve relevant chunks with hybrid search and PageIndex fallback.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict, 'source': str}
    """
    if top_k <= 0 or not query.strip():
        return []

    dense_results = semantic_search(query, top_k=top_k * 2)
    sparse_results = lexical_search(query, top_k=top_k * 2)

    merged = rerank_rrf([dense_results, sparse_results], top_k=top_k * 2)
    merged = _with_source(merged, "hybrid")

    if use_reranking and merged:
        final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
        final_results = _with_source(final_results, "hybrid")
    else:
        final_results = merged[:top_k]

    best_score = final_results[0]["score"] if final_results else 0.0
    if not final_results or best_score < score_threshold:
        return pageindex_search(query, top_k=top_k)

    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma túy",
        "Nghệ sĩ nào bị bắt vì sử dụng ma túy",
        "Luật phòng chống ma túy 2021 quy định gì về cai nghiện",
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        for i, result in enumerate(retrieve(q, top_k=3), start=1):
            print(f"{i}. [{result['score']:.3f}] [{result['source']}] {result['content'][:80]}...")
