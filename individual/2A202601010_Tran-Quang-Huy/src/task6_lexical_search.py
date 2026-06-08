"""
Task 6: lexical search using BM25.

BM25 rewards exact keyword matches, discounts common words with IDF, and
normalizes document length. This complements Task 5's cosine retrieval.
"""

import re
from functools import lru_cache

from rank_bm25 import BM25Okapi

from src.task4_chunking_indexing import chunk_documents, load_documents

TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
CORPUS: list[dict] = []


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def build_bm25_index(corpus: list[dict]) -> BM25Okapi:
    """Build a BM25 index from chunk dictionaries."""
    tokenized_corpus = [_tokenize(doc["content"]) for doc in corpus]
    return BM25Okapi(tokenized_corpus)


@lru_cache(maxsize=1)
def _lexical_index():
    global CORPUS
    CORPUS = chunk_documents(load_documents())
    if not CORPUS:
        return [], None
    return CORPUS, build_bm25_index(CORPUS)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Search chunks with BM25.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
    """
    if top_k <= 0 or not query.strip():
        return []

    corpus, bm25 = _lexical_index()
    if not corpus or bm25 is None:
        return []

    scores = bm25.get_scores(_tokenize(query))
    ranked_indices = scores.argsort()[::-1][:top_k]

    results: list[dict] = []
    for idx in ranked_indices:
        score = float(scores[idx])
        if score <= 0:
            continue
        results.append(
            {
                "content": corpus[idx]["content"],
                "score": score,
                "metadata": corpus[idx]["metadata"],
            }
        )

    return results


if __name__ == "__main__":
    for result in lexical_search("Điều 248 tàng trữ trái phép chất ma túy", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
