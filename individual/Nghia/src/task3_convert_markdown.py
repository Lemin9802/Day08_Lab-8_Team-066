"""
Task 3 - Convert files in data/landing/ to Markdown.

MarkItDown is recommended in the assignment, but the current global Python
environment has a pandas/numpy binary mismatch that prevents MarkItDown from
importing. This script uses lightweight local converters instead:

- PDF: pypdf text extraction
- JSON news crawls: content_markdown/content_text fields
- DOCX: minimal XML text extraction from the docx zip

Output keeps the same subdirectory structure under data/standardized/.
"""

from __future__ import annotations

import json
import re
import zipfile
from html import escape
from pathlib import Path
from xml.etree import ElementTree


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def safe_heading(text: str, fallback: str) -> str:
    title = clean_text(text).splitlines()[0] if clean_text(text) else fallback
    title = re.sub(r"^#+\s*", "", title).strip()
    return title or fallback


def convert_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages: list[str] = []

    for index, page in enumerate(reader.pages, 1):
        text = clean_text(page.extract_text() or "")
        if text:
            pages.append(f"## Page {index}\n\n{text}")

    if not pages:
        return (
            f"# {path.stem}\n\n"
            f"Source file: `{path.name}`\n\n"
            "No extractable text was found. This PDF is likely scanned and needs OCR.\n"
        )

    return f"# {path.stem}\n\nSource file: `{path.name}`\n\n" + "\n\n".join(pages) + "\n"


def convert_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")

    root = ElementTree.fromstring(xml_bytes)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []

    for para in root.findall(".//w:p", namespace):
        runs = [node.text or "" for node in para.findall(".//w:t", namespace)]
        text = clean_text("".join(runs))
        if text:
            paragraphs.append(text)

    body = "\n\n".join(paragraphs)
    return f"# {path.stem}\n\nSource file: `{path.name}`\n\n{body}\n"


def convert_json_article(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    title = safe_heading(data.get("title", ""), path.stem)
    url = data.get("url", "N/A")
    crawled = data.get("date_crawled", "N/A")
    source = data.get("source", "N/A")
    content = data.get("content_markdown") or data.get("content_text") or ""

    if not content.strip():
        content = json.dumps(data, ensure_ascii=False, indent=2)

    header = [
        f"# {title}",
        "",
        f"**Source:** {url}",
        f"**Publisher:** {source}",
        f"**Crawled:** {crawled}",
        f"**Original file:** `{path.name}`",
        "",
        "---",
        "",
    ]
    return "\n".join(header) + clean_text(content) + "\n"


def convert_text_like(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in {".html", ".htm"}:
        text = f"```html\n{text}\n```"
    return f"# {path.stem}\n\nSource file: `{escape(path.name)}`\n\n{text}\n"


def output_path_for(input_path: Path) -> Path:
    relative = input_path.relative_to(LANDING_DIR)
    return (OUTPUT_DIR / relative).with_suffix(".md")


def convert_file(path: Path) -> Path | None:
    if path.name.startswith("."):
        return None

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        markdown = convert_pdf(path)
    elif suffix == ".docx":
        markdown = convert_docx(path)
    elif suffix == ".json":
        markdown = convert_json_article(path)
    elif suffix in {".txt", ".md", ".html", ".htm"}:
        markdown = convert_text_like(path)
    else:
        print(f"Skipping unsupported file: {path}")
        return None

    output_path = output_path_for(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def convert_all() -> list[Path]:
    print("=" * 50)
    print("Task 3: Convert landing files to Markdown")
    print("=" * 50)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    converted: list[Path] = []

    for path in sorted(LANDING_DIR.rglob("*")):
        if not path.is_file():
            continue
        output_path = convert_file(path)
        if output_path:
            converted.append(output_path)
            print(f"Saved: {output_path}")

    print(f"\nDone. Converted {len(converted)} files into {OUTPUT_DIR}")
    return converted


if __name__ == "__main__":
    convert_all()
