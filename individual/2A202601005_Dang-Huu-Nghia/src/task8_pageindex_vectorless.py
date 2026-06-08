"""
Task 8 - PageIndex vectorless retrieval.

Real API mode:
    Set USE_PAGEINDEX_API=1 and PAGEINDEX_API_KEY to call PageIndex Cloud.
    Optional PAGEINDEX_DOC_IDS can scope chat to specific uploaded documents.

Local fallback mode:
    If real API mode is not enabled or fails, this module uses a compatible
    local vectorless fallback:

    - Read normalized Markdown documents
    - Preserve heading/page structure
    - Score sections by keyword coverage, phrase hits, title/source matches
    - Return results marked with source="pageindex"

This gives Task 9 a real fallback path without requiring external credentials.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


if load_dotenv:
    load_dotenv()


PROJECT_DIR = Path(__file__).parent.parent
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"
INDEX_DIR = PROJECT_DIR / "data" / "indexes"
PAGEINDEX_LOCAL_PATH = INDEX_DIR / "pageindex_local.json"
PAGEINDEX_UPLOAD_CACHE_PATH = INDEX_DIR / "pageindex_uploaded_docs.json"
PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
PAGEINDEX_API_BASE_URL = os.getenv("PAGEINDEX_API_BASE_URL", "https://api.pageindex.ai").rstrip("/")
USE_PAGEINDEX_API = os.getenv("USE_PAGEINDEX_API") == "1"
PAGEINDEX_DOC_IDS = [
    doc_id.strip()
    for doc_id in os.getenv("PAGEINDEX_DOC_IDS", "").split(",")
    if doc_id.strip()
]

TOKEN_PATTERN = re.compile(r"[\wÀ-ỹ]+", flags=re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text

    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        metadata[key.strip()] = value
    return metadata, text[end + 5 :].lstrip()


def split_markdown_sections(content: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_heading = "Document"
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("#"):
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
                current_lines = []
            current_heading = line.lstrip("#").strip() or current_heading
            current_lines.append(line)
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))
    return [(heading, body) for heading, body in sections if body]


def build_local_pageindex() -> list[dict]:
    entries: list[dict] = []

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if md_file.name.startswith("."):
            continue

        raw_text = md_file.read_text(encoding="utf-8")
        metadata, content = parse_front_matter(raw_text)
        relative_path = md_file.relative_to(STANDARDIZED_DIR).as_posix()
        doc_type = metadata.get("doc_type") or md_file.parent.name
        title = metadata.get("title") or md_file.stem

        for index, (heading, body) in enumerate(split_markdown_sections(content)):
            if len(body.strip()) < 80:
                continue
            entries.append(
                {
                    "content": body.strip(),
                    "metadata": {
                        **metadata,
                        "title": title,
                        "heading": heading,
                        "path": relative_path,
                        "filename": md_file.name,
                        "doc_type": doc_type,
                        "type": doc_type,
                        "section_index": index,
                    },
                }
            )

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    PAGEINDEX_LOCAL_PATH.write_text(
        json.dumps({"entries": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return entries


def pageindex_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"api_key": PAGEINDEX_API_KEY}
    if extra:
        headers.update(extra)
    return headers


def load_cached_doc_ids() -> list[str]:
    if PAGEINDEX_DOC_IDS:
        return PAGEINDEX_DOC_IDS
    if not PAGEINDEX_UPLOAD_CACHE_PATH.exists():
        return []
    try:
        data = json.loads(PAGEINDEX_UPLOAD_CACHE_PATH.read_text(encoding="utf-8"))
        return [item["doc_id"] for item in data.get("documents", []) if item.get("doc_id")]
    except Exception:
        return []


def upload_documents_real() -> list[dict[str, Any]]:
    """
    Upload legal PDFs to PageIndex Cloud and cache returned doc_ids.

    PageIndex's documented document-processing endpoint accepts PDFs and returns
    a doc_id for later chat/retrieval calls.
    """
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("PAGEINDEX_API_KEY is required for real PageIndex upload")

    legal_dir = PROJECT_DIR / "data" / "landing" / "legal"
    uploaded: list[dict[str, Any]] = []

    for pdf_path in sorted(legal_dir.glob("*.pdf")):
        with pdf_path.open("rb") as file:
            response = requests.post(
                f"{PAGEINDEX_API_BASE_URL}/doc/",
                headers=pageindex_headers(),
                files={"file": file},
                timeout=120,
            )
        response.raise_for_status()
        payload = response.json()
        uploaded.append(
            {
                "filename": pdf_path.name,
                "doc_id": payload.get("doc_id"),
                "response": payload,
            }
        )

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    PAGEINDEX_UPLOAD_CACHE_PATH.write_text(
        json.dumps({"documents": uploaded}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return uploaded


def upload_documents():
    """
    Upload documents to real PageIndex when enabled; otherwise build local index.

    Returns:
        Real upload metadata or path to the local index file.
    """
    if USE_PAGEINDEX_API:
        return upload_documents_real()
    build_local_pageindex()
    return PAGEINDEX_LOCAL_PATH


def pageindex_chat_real(query: str) -> dict:
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("PAGEINDEX_API_KEY is required for real PageIndex chat")

    doc_ids = load_cached_doc_ids()
    body: dict[str, Any] = {
        "messages": [{"role": "user", "content": query}],
        "stream": False,
        "temperature": 0,
        "enable_citations": True,
    }
    if doc_ids:
        body["doc_id"] = doc_ids[0] if len(doc_ids) == 1 else doc_ids

    response = requests.post(
        f"{PAGEINDEX_API_BASE_URL}/chat/completions",
        headers=pageindex_headers({"Content-Type": "application/json"}),
        json=body,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def pageindex_search_real(query: str, top_k: int = 5) -> list[dict]:
    payload = pageindex_chat_real(query)
    choices = payload.get("choices", [])
    if not choices:
        return []

    content = choices[0].get("message", {}).get("content", "")
    if not content:
        return []

    return [
        {
            "content": content,
            "score": 1.0,
            "metadata": {
                "provider": "pageindex",
                "mode": "real_api",
                "doc_ids": load_cached_doc_ids(),
                "api_endpoint": f"{PAGEINDEX_API_BASE_URL}/chat/completions",
                "raw_response_id": payload.get("id", ""),
                "usage": payload.get("usage", {}),
            },
            "source": "pageindex",
        }
    ][:top_k]


def load_entries() -> list[dict]:
    if not PAGEINDEX_LOCAL_PATH.exists():
        return build_local_pageindex()
    data = json.loads(PAGEINDEX_LOCAL_PATH.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    if not entries:
        return build_local_pageindex()
    return entries


def score_entry(query: str, entry: dict) -> float:
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0

    query_set = set(query_tokens)
    content = entry.get("content", "")
    metadata = entry.get("metadata", {})
    heading = metadata.get("heading", "")
    title = metadata.get("title", "")
    haystack = f"{title}\n{heading}\n{content}".lower()
    content_tokens = set(tokenize(haystack))

    coverage = len(query_set & content_tokens) / len(query_set)
    phrase_bonus = 0.20 if query.lower() in haystack else 0.0
    heading_bonus = 0.15 * (
        len(query_set & set(tokenize(f"{title} {heading}"))) / len(query_set)
    )
    density = sum(haystack.count(token) for token in query_set) / max(len(content_tokens), 1)

    return coverage + phrase_bonus + heading_bonus + min(density, 0.25)


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval using local PageIndex-style structural matching.

    Returns:
        List of {'content', 'score', 'metadata', 'source': 'pageindex'}
    """
    if top_k <= 0 or not query.strip():
        return []

    if USE_PAGEINDEX_API:
        try:
            return pageindex_search_real(query, top_k=top_k)
        except Exception as exc:
            if os.getenv("PAGEINDEX_STRICT_API") == "1":
                raise
            sys.stderr.write(f"PageIndex real API failed, using local fallback: {exc}\n")

    scored: list[dict] = []
    for entry in load_entries():
        score = score_entry(query, entry)
        if score <= 0:
            continue
        scored.append(
            {
                "content": entry["content"],
                "score": float(score),
                "metadata": entry["metadata"],
                "source": "pageindex",
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    upload_documents()
    for result in pageindex_search("hình phạt sử dụng ma túy", top_k=3):
        preview = result["content"].replace("\n", " ")[:120]
        line = f"[{result['score']:.3f}] {result['metadata'].get('path')}: {preview}...\n"
        sys.stdout.buffer.write(line.encode("utf-8", errors="replace"))
