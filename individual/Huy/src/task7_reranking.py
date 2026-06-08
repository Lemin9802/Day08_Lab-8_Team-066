"""
Task 7: reranking module.

Default reranking is an offline lexical cross-encoder substitute: it scores each
candidate by query-token overlap plus the original retrieval score. MMR and RRF
are included for diversity and fusion experiments.
"""

import math
import re
from collections import Counter

TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def _cosine(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _overlap_score(query: str, content: str) -> float:
    query_counts = Counter(_tokens(query))
    doc_counts = Counter(_tokens(content))
    if not query_counts or not doc_counts:
        return 0.0

    matched = sum(min(count, doc_counts[token]) for token, count in query_counts.items())
    return matched / sum(query_counts.values())


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Offline reranker that approximates cross-encoder behavior with token overlap.

    Returns candidates sorted by a combined relevance score.
    """
    if top_k <= 0:
        return []

    reranked: list[dict] = []
    for candidate in candidates:
        original_score = float(candidate.get("score", 0.0))
        overlap = _overlap_score(query, candidate.get("content", ""))
        combined_score = 0.75 * overlap + 0.25 * original_score
        item = dict(candidate)
        item["score"] = float(combined_score)
        item["rerank_method"] = "local_overlap"
        reranked.append(item)

    reranked.sort(key=lambda item: item["score"], reverse=True)
    return reranked[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance selection.

    MMR = lambda * relevance(query, doc) - (1 - lambda) * similarity(doc, selected)
    """
    if top_k <= 0:
        return []

    selected: list[int] = []
    remaining = list(range(len(candidates)))

    while remaining and len(selected) < top_k:
        best_idx = remaining[0]
        best_score = float("-inf")

        for idx in remaining:
            candidate_embedding = candidates[idx].get("embedding", [])
            relevance = _cosine(query_embedding, candidate_embedding)
            max_selected_sim = 0.0

            for selected_idx in selected:
                selected_embedding = candidates[selected_idx].get("embedding", [])
                max_selected_sim = max(
                    max_selected_sim,
                    _cosine(candidate_embedding, selected_embedding),
                )

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_selected_sim
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        selected.append(best_idx)
        remaining.remove(best_idx)

    results: list[dict] = []
    for idx in selected:
        item = dict(candidates[idx])
        item["score"] = float(item.get("score", 0.0))
        item["rerank_method"] = "mmr"
        results.append(item)
    return results


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion over multiple ranked lists.

    RRF(d) = sum(1 / (k + rank_r(d)))
    """
    scores: dict[str, float] = {}
    item_map: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            key = item.get("metadata", {}).get("path") or item.get("content", "")
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            item_map[key] = item

    results: list[dict] = []
    for key, score in sorted(scores.items(), key=lambda pair: pair[1], reverse=True)[:top_k]:
        item = dict(item_map[key])
        item["score"] = float(score)
        item["rerank_method"] = "rrf"
        results.append(item)

    return results


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",
) -> list[dict]:
    """Unified reranking interface."""
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    if method == "rrf":
        return rerank_rrf([candidates], top_k=top_k)
    if method == "mmr":
        # MMR needs embeddings; fall back to the offline relevance scorer when
        # candidates do not already carry vectors.
        if not candidates or "embedding" not in candidates[0]:
            return rerank_cross_encoder(query, candidates, top_k)
        raise ValueError("Call rerank_mmr(query_embedding, candidates, ...) directly.")
    raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    dummy_candidates = [
        {"content": "Điều 248: tội tàng trữ trái phép chất ma túy", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ bị bắt vì sử dụng ma túy", "score": 0.7, "metadata": {}},
        {"content": "Python programming", "score": 0.6, "metadata": {}},
    ]
    for result in rerank("hình phạt tàng trữ ma túy", dummy_candidates, top_k=2):
        print(f"[{result['score']:.3f}] {result['content']}")
