"""
Task 2: crawl news articles about Vietnamese artists related to drug cases.

Outputs are JSON files in data/landing/news/ with URL, crawl time, title, and
Markdown content. The crawler skips URLs already present in existing JSON files.
"""

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    {
        "url": "https://tuoitre.vn/dien-vien-huu-tin-lanh-7-nam-6-thang-tu-20230428114919793.htm",
        "source_hint": "Tuoi Tre",
    },
    {
        "url": "https://thanhnien.vn/dien-vien-tran-huu-tin-khai-su-dung-ma-tuy-do-to-mo-185230428111023254.htm",
        "source_hint": "Thanh Nien",
    },
    {
        "url": "https://laodong.vn/phap-luat/bat-hoai-thatcher-dien-vien-trong-phim-xin-hay-tin-em-1183674.ldo",
        "source_hint": "Lao Dong",
    },
    {
        "url": "https://tienphong.vn/chan-dung-nu-dien-vien-le-hang-dong-vai-chinh-xin-hay-tin-em-vua-bi-bat-post1528661.tpo",
        "source_hint": "Tien Phong",
    },
    {
        "url": "https://tienphong.vn/hanh-trinh-phe-ma-tuy-roi-giet-nguoi-cua-ca-si-chau-viet-cuong-post1095287.tpo",
        "source_hint": "Tien Phong",
    },
]


def setup_directory() -> None:
    """Create data/landing/news/ if it does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def slugify(text: str, max_len: int = 90) -> str:
    text = text.lower()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-z0-9A-Z_-]+", "-", text)
    text = text.strip("-")
    return text[:max_len] or "article"


def title_from_markdown(markdown: str, fallback: str = "Untitled") -> str:
    """Extract a simple title from Markdown content."""
    for line in markdown.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            return line.lstrip("#").strip() or fallback
        return line[:160]
    return fallback


def existing_urls() -> set[str]:
    """Read URLs already crawled into data/landing/news/."""
    setup_directory()
    urls: set[str] = set()
    for path in DATA_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        url = data.get("url")
        if url:
            urls.add(url)
    return urls


def article_output_path(url: str, title: str) -> Path:
    domain = urlparse(url).netloc.replace("www.", "")
    return DATA_DIR / f"{domain}_{slugify(title)}.json"


def crawl_article_static(url: str, source_hint: str | None = None, error_message: str = "") -> dict:
    """Fallback crawler using requests when browser crawling times out."""
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (compatible; RAGPipelineBot/1.0)"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    title = title or url

    article_node = soup.find("article") or soup.find("main") or soup.body or soup
    lines = [line.strip() for line in article_node.get_text("\n").splitlines()]
    content_lines = [line for line in lines if line]
    markdown = "# " + title + "\n\n" + "\n\n".join(content_lines)
    domain = urlparse(url).netloc.replace("www.", "")

    return {
        "url": url,
        "source_hint": source_hint,
        "domain": domain,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "content_markdown": markdown,
        "success": True,
        "error_message": error_message,
    }


async def crawl_article(url: str, source_hint: str | None = None) -> dict:
    """
    Crawl one article with Crawl4AI.

    Returns:
        {
            "url": str,
            "source_hint": str | None,
            "domain": str,
            "crawled_at": str,
            "title": str,
            "content_markdown": str,
            "success": bool,
            "error_message": str,
        }
    """
    from crawl4ai import AsyncWebCrawler

    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)

        markdown = result.markdown or ""
        if not markdown.strip():
            raise RuntimeError(result.error_message or "Crawl4AI returned empty content")

        title = result.metadata.get("title") if result.metadata else ""
        title = title or title_from_markdown(markdown, fallback=url)
        domain = urlparse(url).netloc.replace("www.", "")

        return {
            "url": url,
            "source_hint": source_hint,
            "domain": domain,
            "crawled_at": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "content_markdown": markdown,
            "success": bool(result.success),
            "error_message": result.error_message or "",
        }
    except Exception as exc:
        return crawl_article_static(url, source_hint=source_hint, error_message=str(exc))


async def crawl_all(force: bool = False) -> list[Path]:
    """Crawl ARTICLE_URLS and save one JSON file per article."""
    setup_directory()
    seen = existing_urls()
    saved_paths: list[Path] = []

    for index, article in enumerate(ARTICLE_URLS, start=1):
        url = article["url"]
        if not force and url in seen:
            print(f"[{index}/{len(ARTICLE_URLS)}] Skipped existing: {url}")
            continue

        print(f"[{index}/{len(ARTICLE_URLS)}] Crawling: {url}")
        data = await crawl_article(url, source_hint=article.get("source_hint"))
        output_path = article_output_path(url, data["title"])
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        saved_paths.append(output_path)
        print(f"  Saved: {output_path}")

    return saved_paths


def list_news_files() -> list[dict]:
    """Return metadata for crawled news JSON files."""
    setup_directory()
    files: list[dict] = []
    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        files.append(
            {
                "filename": path.name,
                "url": data.get("url", ""),
                "title": data.get("title", path.stem),
                "size_bytes": path.stat().st_size,
            }
        )
    return files


if __name__ == "__main__":
    asyncio.run(crawl_all())
