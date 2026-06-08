"""
Task 3: convert files in data/landing/ to Markdown.

Outputs are written to data/standardized/ while preserving subfolders such as
legal/ and news/.
"""

import json
import sys
from pathlib import Path
from typing import Iterable

from markitdown import MarkItDown

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).parent.parent
LANDING_DIR = PROJECT_DIR / "data" / "landing"
OUTPUT_DIR = PROJECT_DIR / "data" / "standardized"

LEGAL_EXTENSIONS = {".pdf", ".docx", ".doc"}
NEWS_EXTENSIONS = {".json", ".html", ".htm", ".txt", ".md"}


def _iter_files(directory: Path, extensions: Iterable[str]) -> list[Path]:
    allowed = {ext.lower() for ext in extensions}
    if not directory.exists():
        return []

    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file()
        and not path.name.startswith(".")
        and path.suffix.lower() in allowed
    )


def _output_path(input_path: Path, input_root: Path, output_root: Path) -> Path:
    relative_path = input_path.relative_to(input_root)
    return (output_root / relative_path).with_suffix(".md")


def _write_markdown(output_path: Path, content: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content.strip() + "\n", encoding="utf-8")


def _display(path: Path) -> str:
    return str(path).encode("utf-8", errors="replace").decode("utf-8")


def _format_news_markdown(data: dict, fallback_title: str) -> str:
    title = data.get("title") or fallback_title
    url = data.get("url", "N/A")
    crawled_at = data.get("date_crawled") or data.get("crawled_at") or "N/A"
    source = data.get("source_hint") or data.get("domain") or "N/A"
    content = (
        data.get("content_markdown")
        or data.get("markdown")
        or data.get("content")
        or data.get("text")
        or ""
    )

    header = [
        f"# {title}",
        "",
        f"**Source:** {source}",
        f"**URL:** {url}",
        f"**Crawled:** {crawled_at}",
        "",
        "---",
        "",
    ]
    return "\n".join(header) + str(content).strip()


def convert_legal_docs() -> None:
    """Convert PDF/DOC/DOCX files in data/landing/legal/ to Markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    converter = MarkItDown()
    for filepath in _iter_files(legal_dir, LEGAL_EXTENSIONS):
        print(f"Converting: {_display(filepath)}")
        output_path = _output_path(filepath, legal_dir, output_dir)
        try:
            result = converter.convert(str(filepath))
            _write_markdown(output_path, result.text_content)
            print(f"  Saved: {_display(output_path)}")
        except Exception as exc:
            print(f"  Failed: {_display(filepath)} ({exc})")


def convert_news_articles() -> None:
    """Convert crawled news files in data/landing/news/ to Markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    converter = MarkItDown()
    for filepath in _iter_files(news_dir, NEWS_EXTENSIONS):
        print(f"Converting: {_display(filepath)}")
        output_path = _output_path(filepath, news_dir, output_dir)
        try:
            suffix = filepath.suffix.lower()
            if suffix == ".json":
                data = json.loads(filepath.read_text(encoding="utf-8"))
                content = _format_news_markdown(data, filepath.stem)
            elif suffix == ".md":
                content = filepath.read_text(encoding="utf-8")
            else:
                result = converter.convert(str(filepath))
                content = result.text_content

            _write_markdown(output_path, content)
            print(f"  Saved: {_display(output_path)}")
        except Exception as exc:
            print(f"  Failed: {_display(filepath)} ({exc})")


def convert_all() -> None:
    """Convert all supported landing files to Markdown."""
    print("=" * 50)
    print("Task 3: Convert to Markdown")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print(f"\nDone. Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
