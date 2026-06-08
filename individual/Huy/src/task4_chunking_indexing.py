"""
Task 4: load Markdown documents, split them into chunks, and persist a local
index for the retrieval modules.

This implementation uses RecursiveCharacterTextSplitter because the corpus is a
mix of legal text and noisy crawled news Markdown. A recursive splitter keeps
paragraph/sentence boundaries when possible, then falls back to smaller
separators so chunk lengths stay predictable.
"""

import json
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

PROJECT_DIR = Path(__file__).parent.parent
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"
INDEX_DIR = PROJECT_DIR / "data" / "index"
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"

# 500 chars keeps each retrieval unit focused enough for citation while still
# carrying a full legal clause or a short news paragraph. 50 chars overlap helps
# preserve context across boundaries without creating too many duplicates.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

# A local TF-IDF vectorizer is used by Task 5 at query time. It is offline,
# deterministic, and lightweight for the classroom test environment.
EMBEDDING_MODEL = "local-tfidf-char-word"
EMBEDDING_DIM = 384
VECTOR_STORE = "local_jsonl"


def _doc_type(path: Path) -> str:
    parts = {part.lower() for part in path.parts}
    if "legal" in parts:
        return "legal"
    if "news" in parts:
        return "news"
    return "unknown"


def load_documents() -> list[dict]:
    """
    Read all Markdown files from data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    documents: list[dict] = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if md_file.name.startswith("."):
            continue

        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        documents.append(
            {
                "content": content,
                "metadata": {
                    "source": md_file.name,
                    "path": str(md_file.relative_to(PROJECT_DIR)),
                    "type": _doc_type(md_file),
                },
            }
        )

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Split documents into bounded chunks.

    Returns:
        List of {'content': str, 'metadata': dict}
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "; ", ", ", " ", ""],
        length_function=len,
    )

    chunks: list[dict] = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for chunk_index, chunk_text in enumerate(splits):
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue

            chunks.append(
                {
                    "content": chunk_text,
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index": chunk_index,
                    },
                }
            )

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Add deterministic lightweight embeddings to chunks.

    The persisted vectors are mainly for inspection and future extension. Task 5
    builds a TF-IDF matrix over the current chunks for query-time similarity.
    """
    from sklearn.feature_extraction.text import HashingVectorizer

    vectorizer = HashingVectorizer(
        n_features=EMBEDDING_DIM,
        alternate_sign=False,
        norm="l2",
        analyzer="char_wb",
        ngram_range=(3, 5),
    )
    matrix = vectorizer.transform([chunk["content"] for chunk in chunks])

    enriched: list[dict] = []
    for chunk, row in zip(chunks, matrix):
        item = dict(chunk)
        item["embedding"] = row.toarray()[0].astype(float).tolist()
        enriched.append(item)

    return enriched


def index_to_vectorstore(chunks: list[dict]) -> Path:
    """Persist chunks to a JSONL file used by later tasks."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    return CHUNKS_PATH


def run_pipeline() -> None:
    """Run load -> chunk -> embed -> local index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\nLoaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"Embedded {len(chunks)} chunks")

    index_path = index_to_vectorstore(chunks)
    print(f"Indexed to {index_path}")


if __name__ == "__main__":
    run_pipeline()
