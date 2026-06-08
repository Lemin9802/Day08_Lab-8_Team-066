"""
Task 8: PageIndex-style vectorless retrieval.

When PAGEINDEX_API_KEY is available, this module uploads PDFs with the official
SDK and queries PageIndex retrieval. A local fallback is kept so tests and demos
still run while uploaded documents are processing.
"""

import json
import os
import re
import time
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pageindex import PageIndexAPIError, PageIndexClient
from rank_bm25 import BM25Okapi

from src.task4_chunking_indexing import CHUNKS_PATH, chunk_documents, load_documents

load_dotenv()

PROJECT_DIR = Path(__file__).parent.parent
PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"
LANDING_LEGAL_DIR = PROJECT_DIR / "data" / "landing" / "legal"
PAGEINDEX_DIR = PROJECT_DIR / "data" / "pageindex"
MANIFEST_PATH = PAGEINDEX_DIR / "documents.json"
TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def _load_chunks() -> list[dict]:
    if CHUNKS_PATH.exists():
        chunks: list[dict] = []
        for line in CHUNKS_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                chunks.append(json.loads(line))
        if chunks:
            return chunks

    return chunk_documents(load_documents())


def _client() -> PageIndexClient | None:
    if not PAGEINDEX_API_KEY:
        return None
    return PageIndexClient(api_key=PAGEINDEX_API_KEY)


def _load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"documents": []}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _save_manifest(manifest: dict) -> None:
    PAGEINDEX_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _pdf_files() -> list[Path]:
    if not LANDING_LEGAL_DIR.exists():
        return []
    return sorted(path for path in LANDING_LEGAL_DIR.glob("*.pdf") if path.is_file())


@lru_cache(maxsize=1)
def _local_pageindex():
    chunks = _load_chunks()
    if not chunks:
        return [], None
    bm25 = BM25Okapi([_tokenize(chunk["content"]) for chunk in chunks])
    return chunks, bm25


def upload_documents(force: bool = False) -> list[dict]:
    """
    Upload legal PDF documents to PageIndex and save their doc_id in a manifest.

    PageIndex Cloud SDK accepts PDF files, so this function uploads PDFs from
    data/landing/legal/. Existing manifest entries are reused unless force=True.
    """
    client = _client()
    if client is None:
        return []

    manifest = _load_manifest()
    existing = {
        item["path"]: item
        for item in manifest.get("documents", [])
        if item.get("path") and item.get("doc_id")
    }

    uploaded: list[dict] = []
    for pdf_path in _pdf_files():
        relative_path = str(pdf_path.relative_to(PROJECT_DIR))
        if not force and relative_path in existing:
            uploaded.append(existing[relative_path])
            continue

        result = client.submit_document(str(pdf_path))
        item = {
            "filename": pdf_path.name,
            "path": relative_path,
            "doc_id": result["doc_id"],
            "type": "legal",
        }
        existing[relative_path] = item
        uploaded.append(item)

    manifest["documents"] = list(existing.values())
    _save_manifest(manifest)
    return uploaded


def _parse_retrieved_nodes(result: dict, doc_meta: dict, top_k: int) -> list[dict]:
    nodes = result.get("retrieved_nodes") or result.get("nodes") or result.get("results") or []
    parsed: list[dict] = []

    for rank, node in enumerate(nodes[:top_k], start=1):
        if isinstance(node, str):
            content = node
            metadata = {}
            score = 1.0 / rank
        else:
            relevant_contents = node.get("relevant_contents") or []
            extracted_parts: list[str] = []
            for group in relevant_contents:
                if not isinstance(group, list):
                    continue
                for item in group:
                    if not isinstance(item, dict):
                        continue
                    section_title = item.get("section_title") or node.get("title") or ""
                    relevant_content = item.get("relevant_content") or ""
                    if relevant_content:
                        extracted_parts.append(
                            f"{section_title}\n{relevant_content}".strip()
                        )

            content = (
                "\n\n".join(extracted_parts)
                or node.get("text")
                or node.get("content")
                or node.get("markdown")
                or node.get("summary")
                or json.dumps(node, ensure_ascii=False)
            )
            raw_metadata = node.get("metadata") or {}
            metadata = raw_metadata if isinstance(raw_metadata, dict) else {"raw_metadata": raw_metadata}
            if node.get("id"):
                metadata["node_id"] = node["id"]
            if node.get("title"):
                metadata["title"] = node["title"]
            score = float(node.get("score") or node.get("relevance_score") or 1.0 / rank)

        parsed.append(
            {
                "content": content,
                "score": score,
                "metadata": {
                    **metadata,
                    "source": doc_meta.get("filename", "pageindex_document"),
                    "path": doc_meta.get("path", ""),
                    "doc_id": doc_meta.get("doc_id", ""),
                    "type": doc_meta.get("type", "legal"),
                },
                "source": "pageindex",
            }
        )

    return parsed


def _pageindex_search_remote(query: str, top_k: int = 5, timeout_seconds: int = 8) -> list[dict]:
    client = _client()
    if client is None:
        return []

    manifest = _load_manifest()
    documents = [doc for doc in manifest.get("documents", []) if doc.get("doc_id")]
    if not documents:
        documents = upload_documents()

    results: list[dict] = []
    deadline = time.time() + timeout_seconds

    for doc in documents:
        doc_id = doc["doc_id"]
        if not client.is_retrieval_ready(doc_id):
            continue

        retrieval = client.submit_query(doc_id, query)
        retrieval_id = retrieval["retrieval_id"]

        while time.time() < deadline:
            result = client.get_retrieval(retrieval_id)
            status = str(result.get("status", "")).lower()
            if status in {"completed", "complete", "success", "succeeded"} or result.get("retrieved_nodes"):
                results.extend(_parse_retrieved_nodes(result, doc, top_k))
                break
            if status in {"failed", "error"}:
                break
            time.sleep(1)

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval fallback.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict, 'source': 'pageindex'}
    """
    if top_k <= 0 or not query.strip():
        return []

    try:
        remote_results = _pageindex_search_remote(query, top_k=top_k)
        if remote_results:
            return remote_results
    except (PageIndexAPIError, OSError, ValueError, KeyError):
        pass

    chunks, bm25 = _local_pageindex()
    if not chunks or bm25 is None:
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
                "content": chunks[idx]["content"],
                "score": score,
                "metadata": chunks[idx]["metadata"],
                "source": "pageindex",
            }
        )

    return results


if __name__ == "__main__":
    uploaded = upload_documents()
    print(f"Prepared {len(uploaded)} documents for PageIndex-style retrieval.")
    for result in pageindex_search("hình phạt sử dụng ma túy", top_k=3):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
