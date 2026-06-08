"""
Task 5 - Semantic search over the Task 4 local vector store.

The search uses the same deterministic hashing embedding from Task 4 and cosine
similarity against vectors stored in data/indexes/vector_store.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from src.task4_chunking_indexing import VECTOR_STORE_PATH, hashing_embedding, run_pipeline
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.task4_chunking_indexing import VECTOR_STORE_PATH, hashing_embedding, run_pipeline


def load_vector_store() -> list[dict]:
    if not VECTOR_STORE_PATH.exists():
        run_pipeline()

    data = json.loads(VECTOR_STORE_PATH.read_text(encoding="utf-8"))
    return data.get("chunks", [])


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Search chunks with vector similarity.

    Args:
        query: Search query.
        top_k: Maximum number of results.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}, sorted by
        score descending.
    """
    if top_k <= 0:
        return []

    query = query.strip()
    if not query:
        return []

    chunks = load_vector_store()
    query_embedding = hashing_embedding(query)

    results: list[dict] = []
    for chunk in chunks:
        score = cosine_similarity(query_embedding, chunk.get("embedding", []))
        results.append(
            {
                "content": chunk.get("content", ""),
                "score": float(score),
                "metadata": chunk.get("metadata", {}),
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for result in semantic_search("hình phạt cho tội tàng trữ ma túy", top_k=5):
        source = result["metadata"].get("path", "unknown")
        preview = result["content"].replace("\n", " ")[:120]
        line = f"[{result['score']:.3f}] {source}: {preview}...\n"
        sys.stdout.buffer.write(line.encode("utf-8", errors="replace"))
