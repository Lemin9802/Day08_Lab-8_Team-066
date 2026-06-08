"""
Task 10 - Generation with citations.

This module supports two modes:
    - If OPENAI_API_KEY is set, call OpenAI with a citation-focused prompt.
    - Otherwise, generate a deterministic extractive answer from retrieved
      chunks. This keeps the assignment runnable without external credentials.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    from src.task9_retrieval_pipeline import retrieve
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.task9_retrieval_pipeline import retrieve


if load_dotenv:
    load_dotenv()


# top_k=5 is enough to provide multiple supporting chunks while keeping the
# prompt compact. top_p=0.9 allows limited variation for LLM mode; temperature
# 0.3 keeps legal/news answers factual.
TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3


SYSTEM_PROMPT = """Answer the question in Vietnamese using only the provided context.
Every factual claim must include a citation in square brackets.
If the context is insufficient, say: Tôi không thể xác minh thông tin này từ nguồn hiện có."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Reorder chunks to reduce "lost in the middle".

    Keep the highest-scoring chunk first, put alternating important chunks near
    the beginning/end, and leave lower-priority chunks in the middle.
    Example: [1, 2, 3, 4, 5] -> [1, 3, 5, 4, 2]
    """
    if len(chunks) <= 2:
        return chunks

    reordered: list[dict] = []
    for index in range(0, len(chunks), 2):
        reordered.append(chunks[index])

    last_even_index = len(chunks) - 1 if len(chunks) % 2 == 0 else len(chunks) - 2
    for index in range(last_even_index, 0, -2):
        reordered.append(chunks[index])

    return reordered


def citation_label(chunk: dict, fallback_index: int = 1) -> str:
    metadata = chunk.get("metadata", {})
    title = metadata.get("title") or metadata.get("source") or metadata.get("filename")
    path = metadata.get("path") or metadata.get("source_file") or metadata.get("url")
    heading = metadata.get("heading")
    chunk_index = metadata.get("chunk_index")
    year = extract_year(chunk)

    source = title or path or f"Source {fallback_index}"
    if path and not title:
        source = Path(str(path)).stem

    base = f"{source}, {year}" if year else str(source)
    if heading and heading != "Document":
        return f"{base}, {heading}"
    if chunk_index is not None:
        return f"{base}, chunk {chunk_index}"
    return base


def extract_year(chunk: dict) -> str:
    metadata = chunk.get("metadata", {})
    candidates = [
        metadata.get("published_at", ""),
        metadata.get("date_published", ""),
        metadata.get("title", ""),
        chunk.get("content", "")[:500],
        metadata.get("date_crawled", ""),
        metadata.get("source", ""),
        metadata.get("source_file", ""),
        metadata.get("path", ""),
        metadata.get("url", ""),
    ]
    for value in candidates:
        match = re.search(r"\b(20\d{2}|19\d{2})\b", str(value))
        if match:
            return match.group(1)
    return ""


def format_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks with source labels suitable for citation.
    """
    parts: list[str] = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source") or metadata.get("source_file") or metadata.get("path") or f"Source {index}"
        doc_type = metadata.get("type") or metadata.get("doc_type") or "unknown"
        label = citation_label(chunk, index)
        score = float(chunk.get("score", 0.0))
        content = chunk.get("content", "").strip()
        parts.append(
            f"[Document {index} | Citation: {label} | Source: {source} | Type: {doc_type} | Score: {score:.3f}]\n"
            f"{content}"
        )
    return "\n\n---\n\n".join(parts)


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*Source:\*\*\s+\S+", "", text)
    text = re.sub(r"Source file:\s+`[^`]+`", "", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?。])\s+|\n+", text)
    return [sentence.strip(" -") for sentence in sentences if len(sentence.strip()) > 30]


def query_terms(query: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[\wÀ-ỹ]+", query, flags=re.UNICODE) if len(token) > 2}


def sentence_score(sentence: str, terms: set[str]) -> int:
    lowered = sentence.lower()
    return sum(1 for term in terms if term in lowered)


def build_extractive_answer(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return "Tôi không thể xác minh thông tin này từ nguồn hiện có."

    terms = query_terms(query)
    selected: list[tuple[str, str, int]] = []

    for index, chunk in enumerate(chunks, 1):
        label = citation_label(chunk, index)
        sentences = split_sentences(chunk.get("content", ""))
        ranked = sorted(
            sentences,
            key=lambda sentence: sentence_score(sentence, terms),
            reverse=True,
        )
        for sentence in ranked[:2]:
            score = sentence_score(sentence, terms)
            if score > 0:
                selected.append((sentence, label, score))

    selected.sort(key=lambda item: item[2], reverse=True)
    unique: list[tuple[str, str]] = []
    seen = set()
    for sentence, label, _ in selected:
        key = sentence.lower()
        if key in seen:
            continue
        unique.append((sentence, label))
        seen.add(key)
        if len(unique) >= 4:
            break

    if not unique:
        return "Tôi không thể xác minh thông tin này từ nguồn hiện có."

    answer_lines = ["Dựa trên các nguồn đã truy xuất:"]
    for sentence, label in unique:
        answer_lines.append(f"- {sentence} [{label}]")
    return "\n".join(answer_lines)


def call_openai_generation(query: str, context: str) -> str | None:
    if os.getenv("USE_OPENAI_GENERATION") != "1":
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return response.choices[0].message.content or ""
    except Exception:
        return None


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation with citations.

    Returns:
        {
            'answer': str,
            'sources': list[dict],
            'retrieval_source': str,
            'context': str,
        }
    """
    chunks = retrieve(query, top_k=top_k)
    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)

    answer = call_openai_generation(query, context)
    if not answer:
        answer = build_extractive_answer(query, reordered)

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "none") if chunks else "none",
        "context": context,
    }


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma túy theo pháp luật Việt Nam?",
        "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma túy?",
        "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma túy 2021?",
    ]

    for question in test_queries:
        result = generate_with_citation(question)
        sys.stdout.buffer.write(f"\nQ: {question}\n".encode("utf-8"))
        sys.stdout.buffer.write(f"A: {result['answer']}\n".encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(
            f"[Sources: {len(result['sources'])} | via {result['retrieval_source']}]\n".encode("utf-8")
        )
