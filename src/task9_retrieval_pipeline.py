"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp:
    - Task 5: semantic_search
    - Task 6: lexical_search / BM25
    - Task 7: RRF + lightweight rerank
    - Task 8: PageIndex/local vectorless fallback

Pipeline:
    1. Chạy semantic_search + lexical_search
    2. Merge bằng RRF
    3. Rerank query-aware
    4. Nếu kết quả yếu thì fallback sang PageIndex/local vectorless
    5. Return top_k results
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_TOP_K = 5

# Vì sau RRF + query_overlap rerank, score nằm khoảng 0 → 1.
# 0.15 là ngưỡng vừa phải: query quá lệch corpus thì fallback PageIndex.
SCORE_THRESHOLD = 0.15

# Dùng query_overlap vì local, nhẹ, không cần cross-encoder/API.
# Flow vẫn là: RRF merge trước, query-aware rerank sau.
RERANK_METHOD = "query_overlap"


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với fallback logic.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả cuối cùng
        score_threshold: Ngưỡng điểm tối thiểu cho hybrid results
        use_reranking: Có áp dụng reranking hay không

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': str
        }
    """
    if not query or not query.strip():
        return []

    print(f"Retrieving for query: {query}")

    # -------------------------------------------------------------------------
    # Step 1: Chạy semantic search + lexical search
    # -------------------------------------------------------------------------
    dense_results = semantic_search(query, top_k=top_k * 3)
    sparse_results = lexical_search(query, top_k=top_k * 3)

    print(f"  Dense results: {len(dense_results)}")
    print(f"  Sparse results: {len(sparse_results)}")

    # -------------------------------------------------------------------------
    # Step 2: Merge bằng RRF
    # -------------------------------------------------------------------------
    merged_results = rerank_rrf(
        ranked_lists=[dense_results, sparse_results],
        top_k=top_k * 3,
    )

    for item in merged_results:
        item["source"] = "hybrid"

    print(f"  Merged results: {len(merged_results)}")

    # -------------------------------------------------------------------------
    # Step 3: Rerank
    # -------------------------------------------------------------------------
    if use_reranking and merged_results:
        final_results = rerank(
            query=query,
            candidates=merged_results,
            top_k=top_k,
            method=RERANK_METHOD,
        )
    else:
        final_results = merged_results[:top_k]

    for item in final_results:
        item["source"] = "hybrid"

    best_score = final_results[0]["score"] if final_results else 0.0
    print(f"  Best hybrid score: {best_score:.4f}")

    # -------------------------------------------------------------------------
    # Step 4: Fallback PageIndex nếu không đủ tốt
    # -------------------------------------------------------------------------
    if not final_results or best_score < score_threshold:
        print(
            f"  ⚠ Hybrid score thấp hơn threshold "
            f"({best_score:.4f} < {score_threshold:.4f}). "
            f"Fallback → PageIndex/local vectorless"
        )

        fallback_results = pageindex_search(query, top_k=top_k)

        for item in fallback_results:
            item["source"] = item.get("source", "pageindex_local")

        return fallback_results[:top_k]

    # -------------------------------------------------------------------------
    # Step 5: Return top_k
    # -------------------------------------------------------------------------
    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "danh mục chất ma túy và tiền chất theo Nghị định 28/2026",
        "tiêu chí xác định địa bàn trọng điểm phức tạp về ma túy",
        "cơ sở cai nghiện bắt buộc",
        "ca sĩ Miu Lê bị bắt sử dụng ma túy",
        "rapper Bình Gold dương tính ma túy",
    ]

    for query in test_queries:
        print("\n" + "=" * 80)
        print(f"Query: {query}")
        print("-" * 80)

        results = retrieve(query, top_k=3)

        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            score = result.get("score", 0.0)
            result_source = result.get("source", "unknown")
            doc_source = metadata.get("source", "unknown")
            doc_type = metadata.get("type", "unknown")
            preview = result.get("content", "")[:220].replace("\n", " ")

            print(
                f"{i}. score={score:.4f} | retrieval={result_source} "
                f"| type={doc_type} | source={doc_source}"
            )
            print(f"   {preview}...")