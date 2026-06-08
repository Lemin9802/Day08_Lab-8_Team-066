"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.

Yêu cầu:
    1. Scan toàn bộ file trong data/landing/ gồm PDF, DOCX, JSON.
    2. Convert sang Markdown.
    3. Lưu vào data/standardized/ và giữ nguyên cấu trúc thư mục:
       - data/standardized/legal/
       - data/standardized/news/
"""

import json
from pathlib import Path

from markitdown import MarkItDown


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def get_markitdown_text(result) -> str:
    """
    MarkItDown thường trả về result.text_content.
    Hàm này giúp tránh lỗi nếu version khác một chút.
    """
    if hasattr(result, "text_content"):
        return result.text_content
    return str(result)


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown()
    converted_count = 0

    if not legal_dir.exists():
        raise FileNotFoundError(f"Không tìm thấy thư mục: {legal_dir}")

    for filepath in legal_dir.iterdir():
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting legal doc: {filepath.name}")

            try:
                result = md.convert(str(filepath))
                text_content = get_markitdown_text(result).strip()

                output_path = output_dir / f"{filepath.stem}.md"

                markdown = f"# {filepath.stem}\n\n"
                markdown += f"**Source file:** {filepath.name}\n\n"
                markdown += "---\n\n"
                markdown += text_content

                output_path.write_text(markdown, encoding="utf-8")
                print(f"  ✓ Saved: {output_path} ({len(markdown)} chars)")

                if len(text_content) < 500:
                    print("  ⚠ Nội dung convert hơi ngắn, nên mở file markdown kiểm tra lại.")

                converted_count += 1

            except Exception as exc:
                print(f"  ✗ Failed to convert {filepath.name}")
                print(f"    Error: {exc}")

    print(f"✓ Converted {converted_count} legal documents")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    converted_count = 0

    if not news_dir.exists():
        raise FileNotFoundError(f"Không tìm thấy thư mục: {news_dir}")

    for filepath in news_dir.iterdir():
        if filepath.suffix.lower() == ".json":
            print(f"Converting news article: {filepath.name}")

            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))

                title = data.get("title", "Unknown")
                url = data.get("url", "N/A")
                date_crawled = data.get("date_crawled", "N/A")
                content_markdown = data.get("content_markdown", "").strip()

                output_path = output_dir / f"{filepath.stem}.md"

                markdown = f"# {title}\n\n"
                markdown += f"**Source:** {url}\n\n"
                markdown += f"**Crawled:** {date_crawled}\n\n"
                markdown += f"**Source file:** {filepath.name}\n\n"
                markdown += "---\n\n"
                markdown += content_markdown

                output_path.write_text(markdown, encoding="utf-8")
                print(f"  ✓ Saved: {output_path} ({len(markdown)} chars)")

                if len(content_markdown) < 500:
                    print("  ⚠ Nội dung bài báo hơi ngắn, nên kiểm tra lại file JSON.")

                converted_count += 1

            except Exception as exc:
                print(f"  ✗ Failed to convert {filepath.name}")
                print(f"    Error: {exc}")

    print(f"✓ Converted {converted_count} news articles")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 60)
    print("Task 3: Convert to Markdown")
    print("=" * 60)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\n✓ Done! Output tại:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()