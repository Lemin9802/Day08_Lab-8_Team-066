"""
Task 7 - Reranking module.

Default method: local relevance reranking. It blends the original retrieval
score with query/document token overlap, giving a simple cross-encoder-like
second pass without external APIs.

Also includes:
    - MMR for relevance/diversity selection
    - RRF for fusing multiple ranked lists
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path


try:
    from src.task4_chunking_indexing import hashing_embedding
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.task4_chunking_indexing import hashing_embedding


TOKEN_PATTERN = re.compile(r"[\wÀ-ỹ]+", flags=re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def cosine_sim(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def normalize_scores(values: list[float]) -> list[float]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if high == low:
        return [1.0 if high > 0 else 0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def token_overlap_score(query: str, content: str) -> float:
    query_terms = set(tokenize(query))
    if not query_terms:
        return 0.0
    content_terms = set(tokenize(content))
    return len(query_terms & content_terms) / len(query_terms)


def rerank_cross_encoder(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Local cross-encoder-style relevance reranker.

    The score combines:
        - normalized initial retrieval score
        - query token coverage in the candidate text
        - hashing-vector cosine similarity
    """
    if top_k <= 0 or not candidates:
        return []

    query_embedding = hashing_embedding(query)
    original_scores = normalize_scores([float(item.get("score", 0.0)) for item in candidates])

    reranked: list[dict] = []
    for index, candidate in enumerate(candidates):
        content = candidate.get("content", "")
        overlap = token_overlap_score(query, content)
        semantic = cosine_sim(query_embedding, hashing_embedding(content))
        original = original_scores[index]
        score = 0.50 * overlap + 0.30 * semantic + 0.20 * original

        item = candidate.copy()
        item["score"] = float(score)
        item["rerank_score"] = float(score)
        item["metadata"] = dict(candidate.get("metadata", {}))
        item["metadata"]["rerank_method"] = "local_relevance"
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
    Maximal Marginal Relevance.

    MMR = lambda * relevance_to_query - (1-lambda) * similarity_to_selected
    """
    if top_k <= 0 or not candidates:
        return []

    candidate_embeddings = [
        candidate.get("embedding") or hashing_embedding(candidate.get("content", ""))
        for candidate in candidates
    ]
    selected: list[int] = []
    remaining = list(range(len(candidates)))

    while remaining and len(selected) < top_k:
        best_index = remaining[0]
        best_score = float("-inf")

        for index in remaining:
            relevance = cosine_sim(query_embedding, candidate_embeddings[index])
            diversity_penalty = 0.0
            if selected:
                diversity_penalty = max(
                    cosine_sim(candidate_embeddings[index], candidate_embeddings[selected_index])
                    for selected_index in selected
                )
            score = lambda_param * relevance - (1 - lambda_param) * diversity_penalty
            if score > best_score:
                best_score = score
                best_index = index

        selected.append(best_index)
        remaining.remove(best_index)

    results = []
    for index in selected:
        item = candidates[index].copy()
        item["score"] = float(cosine_sim(query_embedding, candidate_embeddings[index]))
        item["metadata"] = dict(item.get("metadata", {}))
        item["metadata"]["rerank_method"] = "mmr"
        results.append(item)
    return results


def item_key(item: dict) -> str:
    metadata = item.get("metadata", {})
    return metadata.get("chunk_id") or metadata.get("path", "") + "::" + str(metadata.get("chunk_index", "")) or item.get("content", "")


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    """
    Reciprocal Rank Fusion.

    RRF(d) = sum(1 / (k + rank_r(d))) across ranked lists.
    """
    if top_k <= 0:
        return []

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item_key(item)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            items.setdefault(key, item)

    results: list[dict] = []
    for key, score in sorted(scores.items(), key=lambda pair: pair[1], reverse=True)[:top_k]:
        item = items[key].copy()
        item["score"] = float(score)
        item["rerank_score"] = float(score)
        item["metadata"] = dict(item.get("metadata", {}))
        item["metadata"]["rerank_method"] = "rrf"
        results.append(item)
    return results


def rerank(query: str, candidates: list[dict], top_k: int = 5, method: str = "cross_encoder") -> list[dict]:
    """
    Unified reranking interface.

    method:
        - "cross_encoder": local relevance reranker
        - "mmr": local MMR using hashing embeddings
        - "rrf": treat candidates as one ranked list and return RRF scores
    """
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    if method == "mmr":
        return rerank_mmr(hashing_embedding(query), candidates, top_k)
    if method == "rrf":
        return rerank_rrf([candidates], top_k)
    raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma túy", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ bị bắt vì sử dụng ma túy", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
    ]
    for result in rerank("hình phạt tàng trữ ma túy", dummy_candidates, top_k=2):
        line = f"[{result['score']:.3f}] {result['content']}\n"
        sys.stdout.buffer.write(line.encode("utf-8", errors="replace"))
