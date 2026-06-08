"""
Task 4 - Chunking and indexing standardized Markdown documents.

Design choices:
    - Chunking: recursive character chunking with Markdown-aware separators.
      This keeps sections/paragraphs together when possible and falls back to
      character windows for long legal paragraphs.
    - Chunk size: 800 chars, overlap 100 chars. This is small enough for precise
      legal/news citation while preserving enough context around each clause.
    - Embedding: local hashing vector, 256 dimensions. This avoids downloading
      large models in the current conflicted global Python environment while
      still producing deterministic dense vectors for local semantic search.
    - Vector store: local JSON file at data/indexes/vector_store.json. It is
      simple, inspectable, and works without Docker/Weaviate credentials.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"
INDEX_DIR = PROJECT_DIR / "data" / "indexes"
VECTOR_STORE_PATH = INDEX_DIR / "vector_store.json"


CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
CHUNKING_METHOD = "recursive_character"

EMBEDDING_MODEL = "local-hashing-vector-v1"
EMBEDDING_DIM = 256

VECTOR_STORE = "local_json"


TOKEN_PATTERN = re.compile(r"[\wÀ-ỹ]+", flags=re.UNICODE)
SEPARATORS = ["\n\n", "\n", ". ", "; ", ", ", " "]


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text

    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text

    raw_metadata = text[4:end]
    body = text[end + 5 :].lstrip()
    metadata: dict[str, str] = {}

    for line in raw_metadata.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        metadata[key.strip()] = value

    return metadata, body


def load_documents() -> list[dict]:
    """
    Read all Markdown files from data/standardized/.

    Returns:
        List of {'content': str, 'metadata': dict}
    """
    documents: list[dict] = []

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if md_file.name.startswith("."):
            continue

        raw_text = md_file.read_text(encoding="utf-8")
        metadata, content = parse_front_matter(raw_text)
        relative_path = md_file.relative_to(STANDARDIZED_DIR).as_posix()
        doc_type = metadata.get("doc_type") or md_file.parent.name

        documents.append(
            {
                "content": content.strip(),
                "metadata": {
                    **metadata,
                    "source": metadata.get("source") or metadata.get("source_file") or md_file.name,
                    "path": relative_path,
                    "type": doc_type,
                    "doc_type": doc_type,
                    "filename": md_file.name,
                },
            }
        )

    return documents


def split_long_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    for separator in SEPARATORS:
        parts = text.split(separator)
        if len(parts) == 1:
            continue

        chunks: list[str] = []
        current = ""
        joiner = separator

        for part in parts:
            candidate = part if not current else current + joiner + part
            if len(candidate) <= chunk_size:
                current = candidate
                continue

            if current:
                chunks.extend(split_long_text(current, chunk_size))
            current = part

        if current:
            chunks.extend(split_long_text(current, chunk_size))

        if chunks and all(len(chunk) <= chunk_size for chunk in chunks):
            return chunks

    return [text[start : start + chunk_size] for start in range(0, len(text), chunk_size)]


def apply_overlap(chunks: list[str], overlap: int = CHUNK_OVERLAP) -> list[str]:
    if not chunks or overlap <= 0:
        return chunks

    overlapped = [chunks[0]]
    for previous, current in zip(chunks, chunks[1:]):
        prefix = previous[-overlap:].strip()
        candidate = f"{prefix}\n\n{current}".strip() if prefix else current
        if len(candidate) > CHUNK_SIZE:
            candidate = candidate[-CHUNK_SIZE:]
        overlapped.append(candidate)
    return overlapped


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents with recursive character splitting.

    Returns:
        List of {'content': str, 'metadata': dict}
    """
    chunks: list[dict] = []

    for document in documents:
        content = document["content"].strip()
        if not content:
            continue

        raw_chunks = split_long_text(content)
        raw_chunks = apply_overlap(raw_chunks)

        for index, chunk_text in enumerate(raw_chunks):
            chunk_text = re.sub(r"\n{3,}", "\n\n", chunk_text).strip()
            if not chunk_text:
                continue

            chunks.append(
                {
                    "content": chunk_text,
                    "metadata": {
                        **document["metadata"],
                        "chunk_index": index,
                        "chunk_id": f"{document['metadata']['path']}::chunk-{index:04d}",
                        "chunking_method": CHUNKING_METHOD,
                        "chunk_size": CHUNK_SIZE,
                        "chunk_overlap": CHUNK_OVERLAP,
                    },
                }
            )

    return chunks


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def hashing_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    vector = [0.0] * dim

    for token in tokenize(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [value / norm for value in vector]
    return vector


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Add a deterministic dense vector to every chunk.
    """
    for chunk in chunks:
        chunk["embedding"] = hashing_embedding(chunk["content"])
        chunk["metadata"]["embedding_model"] = EMBEDDING_MODEL
        chunk["metadata"]["embedding_dim"] = EMBEDDING_DIM
    return chunks


def index_to_vectorstore(chunks: list[dict]) -> Path:
    """
    Store chunks and embeddings in a local JSON vector store.
    """
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "config": {
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "chunking_method": CHUNKING_METHOD,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dim": EMBEDDING_DIM,
            "vector_store": VECTOR_STORE,
        },
        "chunks": chunks,
    }
    VECTOR_STORE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return VECTOR_STORE_PATH


def run_pipeline() -> Path:
    """Run the complete load -> chunk -> embed -> index pipeline."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"Embedded {len(chunks)} chunks")

    output_path = index_to_vectorstore(chunks)
    print(f"Indexed to {output_path}")
    return output_path


if __name__ == "__main__":
    run_pipeline()
