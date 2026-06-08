"""
Task 6 - Lexical search with BM25.

BM25 scores chunks by exact term matching:
    - TF: repeated query terms in a chunk increase score.
    - IDF: rarer terms across the corpus are weighted higher.
    - Length normalization: long chunks are not unfairly favored.

The corpus is loaded from the Task 4 local vector store so lexical and semantic
search operate over the same chunks.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path


try:
    from src.task4_chunking_indexing import TOKEN_PATTERN, VECTOR_STORE_PATH, run_pipeline
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.task4_chunking_indexing import TOKEN_PATTERN, VECTOR_STORE_PATH, run_pipeline


CORPUS: list[dict] = []
BM25_INDEX = None
TOKENIZED_CORPUS: list[list[str]] = []


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


class PurePythonBM25:
    """Small BM25Okapi-compatible fallback."""

    def __init__(self, tokenized_corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.tokenized_corpus = tokenized_corpus
        self.k1 = k1
        self.b = b
        self.doc_len = [len(doc) for doc in tokenized_corpus]
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if self.doc_len else 0.0
        self.term_freqs = [Counter(doc) for doc in tokenized_corpus]
        self.idf = self._build_idf()

    def _build_idf(self) -> dict[str, float]:
        doc_count = len(self.tokenized_corpus)
        document_frequency: Counter[str] = Counter()
        for doc in self.tokenized_corpus:
            document_frequency.update(set(doc))

        return {
            term: math.log(1 + (doc_count - freq + 0.5) / (freq + 0.5))
            for term, freq in document_frequency.items()
        }

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores: list[float] = []
        for index, term_freq in enumerate(self.term_freqs):
            doc_len = self.doc_len[index] or 1
            score = 0.0
            for token in query_tokens:
                tf = term_freq.get(token, 0)
                if tf == 0:
                    continue
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / (self.avgdl or 1))
                score += self.idf.get(token, 0.0) * (tf * (self.k1 + 1)) / denominator
            scores.append(score)
        return scores


def load_corpus() -> list[dict]:
    if not VECTOR_STORE_PATH.exists():
        run_pipeline()

    data = json.loads(VECTOR_STORE_PATH.read_text(encoding="utf-8"))
    chunks = data.get("chunks", [])
    return [
        {
            "content": chunk.get("content", ""),
            "metadata": chunk.get("metadata", {}),
        }
        for chunk in chunks
        if chunk.get("content")
    ]


def build_bm25_index(corpus: list[dict]):
    """
    Build a BM25 index from a list of {'content': str, 'metadata': dict}.
    """
    global TOKENIZED_CORPUS

    TOKENIZED_CORPUS = [tokenize(doc["content"]) for doc in corpus]

    try:
        from rank_bm25 import BM25Okapi

        return BM25Okapi(TOKENIZED_CORPUS)
    except Exception:
        return PurePythonBM25(TOKENIZED_CORPUS)


def get_index():
    global BM25_INDEX, CORPUS

    if BM25_INDEX is None:
        CORPUS = load_corpus()
        BM25_INDEX = build_bm25_index(CORPUS)
    return BM25_INDEX


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Search chunks with BM25 lexical matching.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}, sorted by
        score descending.
    """
    if top_k <= 0:
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    bm25 = get_index()
    scores = list(bm25.get_scores(query_tokens))
    ranked_indices = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)

    results: list[dict] = []
    for index in ranked_indices[:top_k]:
        score = float(scores[index])
        results.append(
            {
                "content": CORPUS[index]["content"],
                "score": score,
                "metadata": CORPUS[index]["metadata"],
            }
        )

    return results


if __name__ == "__main__":
    for result in lexical_search("Điều 248 tàng trữ trái phép chất ma túy", top_k=5):
        source = result["metadata"].get("path", "unknown")
        preview = result["content"].replace("\n", " ")[:120]
        line = f"[{result['score']:.3f}] {source}: {preview}...\n"
        sys.stdout.buffer.write(line.encode("utf-8", errors="replace"))
