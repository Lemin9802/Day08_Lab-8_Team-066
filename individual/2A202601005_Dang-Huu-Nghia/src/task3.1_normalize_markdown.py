"""
Normalize Markdown files produced by Task 3 for downstream RAG tasks.

The script keeps information that matters for retrieval and citation while
removing repeated whitespace and common news-site boilerplate.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"
LANDING_NEWS_DIR = PROJECT_DIR / "data" / "landing" / "news"


BOILERPLATE_PATTERNS = [
    r"^bạn cần biết$",
    r"^tiện ích$",
    r"^liên hệ$",
    r"^theo dõi báo",
    r"^quảng cáo$",
    r"^đặt báo$",
    r"^đăng nhập$",
    r"^đóng menu$",
    r"^chia sẻ$",
    r"^bình luận",
    r"^gửi bình luận$",
    r"^xem thêm bình luận$",
    r"^quan tâm nhất",
    r"^khám phá thêm",
    r"^tin liên quan$",
    r"^đọc tiếp$",
    r"^xem thêm$",
    r"^hotline$",
    r"^rss$",
    r"^tòa soạn$",
    r"^chính sách bảo mật$",
    r"^thông tin tài khoản",
    r"^đổi mật khẩu",
    r"^tin đã lưu",
    r"^tin đã xem",
    r"^đăng xuất$",
]

SECTION_NAMES = {
    "chính trị",
    "thời sự",
    "thế giới",
    "kinh tế",
    "đời sống",
    "sức khỏe",
    "sức khoẻ",
    "giới trẻ",
    "giáo dục",
    "du lịch",
    "văn hóa",
    "văn hoá",
    "giải trí",
    "thể thao",
    "công nghệ",
    "xe",
    "video",
    "tiêu dùng",
    "thời trang trẻ",
    "bạn đọc",
    "rao vặt",
}


def normalize_spaces(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_existing_front_matter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :].lstrip()
    return text


def yaml_escape(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def front_matter(metadata: dict[str, str]) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        lines.append(f"{key}: {yaml_escape(str(value))}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def clean_line(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    return line


def is_boilerplate(line: str) -> bool:
    value = clean_line(line).lower()
    if not value:
        return True
    if value in SECTION_NAMES:
        return True
    if len(value) <= 2:
        return True
    return any(re.search(pattern, value) for pattern in BOILERPLATE_PATTERNS)


def find_article_start(lines: list[str], title: str) -> int:
    title_key = clean_line(title).lower()
    candidates = [
        index
        for index, line in enumerate(lines)
        if title_key and clean_line(line).lower() == title_key
    ]
    if not candidates:
        return 0

    date_pattern = re.compile(r"\d{1,2}[./]\d{1,2}[./]\d{4}|\d{1,2}/\d{1,2}/\d{4}")
    for index in candidates:
        window = " ".join(lines[index : index + 8])
        if date_pattern.search(window):
            return index
    return candidates[-1]


def clean_news_body(raw_text: str, title: str) -> str:
    lines = [clean_line(line) for line in raw_text.splitlines()]
    lines = [line for line in lines if line]
    start = find_article_start(lines, title)
    lines = lines[start:]

    cleaned: list[str] = []
    seen_recent: set[str] = set()
    stop_patterns = [
        r"^tin liên quan$",
        r"^chia sẻ$",
        r"^bình luận",
        r"^khám phá thêm",
        r"^chính trị thời sự thế giới",
        r"^đặt báo quảng cáo rss",
    ]

    for line in lines:
        key = line.lower()
        if len(cleaned) >= 6 and any(re.search(pattern, key) for pattern in stop_patterns):
            break
        if is_boilerplate(line):
            continue
        if key.startswith("ảnh:") or key.startswith("video:"):
            continue
        if key in seen_recent:
            continue
        cleaned.append(line)
        seen_recent.add(key)
        if len(seen_recent) > 40:
            seen_recent = set(list(seen_recent)[-20:])

    if cleaned and cleaned[0].lower() == title.lower():
        cleaned = cleaned[1:]

    paragraphs = []
    for line in cleaned:
        if re.match(r"^\d{1,2}[./]\d{1,2}[./]\d{4}", line) or re.search(
            r"GMT\+\d", line
        ):
            paragraphs.append(f"**Published:** {line}")
        else:
            paragraphs.append(line)

    return normalize_spaces("\n\n".join(paragraphs))


def normalize_news_file(path: Path) -> None:
    source_json = LANDING_NEWS_DIR / f"{path.stem}.json"
    if not source_json.exists():
        normalize_generic_file(path, doc_type="news")
        return

    data = json.loads(source_json.read_text(encoding="utf-8"))
    title = data.get("title") or path.stem
    body = clean_news_body(data.get("content_text") or data.get("content_markdown") or "", title)
    if not body:
        body = normalize_spaces(data.get("content_markdown") or "")

    metadata = {
        "title": title,
        "doc_type": "news",
        "source": data.get("source", ""),
        "url": data.get("url", ""),
        "date_crawled": data.get("date_crawled", ""),
        "normalized_at": datetime.now(timezone.utc).isoformat(),
    }

    markdown = (
        front_matter(metadata)
        + f"# {title}\n\n"
        + f"**Source:** {data.get('url', 'N/A')}\n\n"
        + body
        + "\n"
    )
    path.write_text(normalize_spaces(markdown) + "\n", encoding="utf-8")


def normalize_legal_file(path: Path) -> None:
    text = strip_existing_front_matter(path.read_text(encoding="utf-8"))
    text = normalize_spaces(text)
    source_file_match = re.search(r"Source file: `([^`]+)`", text)
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)

    title = title_match.group(1).strip() if title_match else path.stem
    source_file = source_file_match.group(1) if source_file_match else f"{path.stem}.pdf"

    metadata = {
        "title": title,
        "doc_type": "legal",
        "source_file": source_file,
        "normalized_at": datetime.now(timezone.utc).isoformat(),
    }

    text = re.sub(r"\n## Page (\d+)\n", r"\n\n## Page \1\n\n", text)
    text = normalize_spaces(text)
    path.write_text(front_matter(metadata) + text + "\n", encoding="utf-8")


def normalize_generic_file(path: Path, doc_type: str = "document") -> None:
    text = strip_existing_front_matter(path.read_text(encoding="utf-8"))
    text = normalize_spaces(text)
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem
    metadata = {
        "title": title,
        "doc_type": doc_type,
        "normalized_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(front_matter(metadata) + text + "\n", encoding="utf-8")


def normalize_all() -> list[Path]:
    normalized: list[Path] = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if path.name.startswith("."):
            continue
        if path.parent.name == "news":
            normalize_news_file(path)
        elif path.parent.name == "legal":
            normalize_legal_file(path)
        else:
            normalize_generic_file(path)
        normalized.append(path)
        print(f"Normalized: {path}")
    print(f"Done. Normalized {len(normalized)} markdown files.")
    return normalized


if __name__ == "__main__":
    normalize_all()
