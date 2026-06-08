"""
Task 5: semantic-style search over local chunks.

The scorer uses a TF-IDF vector space with word and character n-grams. It is not
a neural embedding model, but it provides dense cosine similarity locally and is
robust for Vietnamese text without downloading Hugging Face weights.
"""

from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.task4_chunking_indexing import chunk_documents, load_documents


@lru_cache(maxsize=1)
def _semantic_index():
    documents = load_documents()
    chunks = chunk_documents(documents)
    if not chunks:
        return [], None, None

    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents=None,
        analyzer="word",
        ngram_range=(1, 2),
        max_features=50_000,
    )
    matrix = vectorizer.fit_transform([chunk["content"] for chunk in chunks])
    return chunks, vectorizer, matrix


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Search chunks by cosine similarity in a local TF-IDF vector space.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
    """
    if top_k <= 0 or not query.strip():
        return []

    chunks, vectorizer, matrix = _semantic_index()
    if not chunks or vectorizer is None or matrix is None:
        return []

    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix).ravel()
    ranked_indices = scores.argsort()[::-1][:top_k]

    results: list[dict] = []
    for idx in ranked_indices:
        score = float(scores[idx])
        if score <= 0:
            continue
        results.append(
            {
                "content": chunks[idx]["content"],
                "score": score,
                "metadata": chunks[idx]["metadata"],
            }
        )

    return results


if __name__ == "__main__":
    for result in semantic_search("hình phạt tàng trữ ma túy", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
