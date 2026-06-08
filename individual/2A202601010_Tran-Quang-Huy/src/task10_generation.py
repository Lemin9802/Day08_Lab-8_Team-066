"""
Task 10: generation with citations.

The default implementation is extractive and offline: it retrieves evidence,
formats sources, and composes a concise Vietnamese answer with citations. This
keeps the pipeline testable without an LLM API key while preserving the RAG
contract. TOP_P and TEMPERATURE are documented for an optional LLM backend.
"""

from .task9_retrieval_pipeline import retrieve

TOP_K = 5

# top_p=0.9 is suitable for optional LLM generation because it allows natural
# phrasing while still limiting low-probability tokens.
TOP_P = 0.9

# temperature=0.3 keeps optional LLM output factual and less creative, which is
# preferred for legal/news RAG with citations.
TEMPERATURE = 0.3

SYSTEM_PROMPT = """Answer in Vietnamese using only the provided context.
Every factual claim must include a citation in brackets.
If the context is insufficient, say: Tôi không thể xác minh thông tin này từ nguồn hiện có."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Reorder chunks to reduce the "lost in the middle" effect.

    Input by score: [1, 2, 3, 4, 5]
    Output:         [1, 3, 5, 4, 2]
    """
    if len(chunks) <= 2:
        return chunks

    first_side = chunks[0::2]
    last_side = chunks[1::2][::-1]
    return first_side + last_side


def _citation_label(chunk: dict, index: int) -> str:
    metadata = chunk.get("metadata", {})
    source = metadata.get("source") or f"Source {index}"
    return source.replace(".md", "")


def format_context(chunks: list[dict]) -> str:
    """
    Format chunks into source-labelled context for citation-aware generation.
    """
    context_parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", f"Source {index}")
        doc_type = metadata.get("type", "unknown")
        score = float(chunk.get("score", 0.0))
        content = chunk.get("content", "").strip()
        context_parts.append(
            f"[Document {index} | Source: {source} | Type: {doc_type} | Score: {score:.3f}]\n"
            f"{content}"
        )
    return "\n\n---\n\n".join(context_parts)


def _summarize_chunk(content: str, max_chars: int = 320) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def _extractive_answer(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return "Tôi không thể xác minh thông tin này từ nguồn hiện có."

    answer_lines = [
        f"Dựa trên các nguồn đã truy xuất cho câu hỏi '{query}', thông tin liên quan nhất như sau:"
    ]
    for index, chunk in enumerate(chunks[:3], start=1):
        citation = _citation_label(chunk, index)
        summary = _summarize_chunk(chunk.get("content", ""))
        if summary:
            answer_lines.append(f"- {summary} [{citation}]")

    if len(answer_lines) == 1:
        return "Tôi không thể xác minh thông tin này từ nguồn hiện có."

    return "\n".join(answer_lines)


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG answer with citations.

    Returns:
        {
            'answer': str,
            'sources': list[dict],
            'retrieval_source': str
        }
    """
    chunks = retrieve(query, top_k=top_k)
    reordered = reorder_for_llm(chunks)
    _ = format_context(reordered)

    answer = _extractive_answer(query, reordered)
    retrieval_source = reordered[0].get("source", "none") if reordered else "none"

    return {
        "answer": answer,
        "sources": reordered,
        "retrieval_source": retrieval_source,
    }


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma túy theo pháp luật Việt Nam?",
        "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma túy?",
        "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma túy 2021?",
    ]

    for q in test_queries:
        print(f"\n{'=' * 70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
