"""
Task 2 - Crawl Vietnamese news articles about artists related to drug cases.

Output:
    data/landing/news/article_01.json, ...

Each JSON file contains:
    url, title, date_crawled, source, content_markdown, content_text
"""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://thanhnien.vn/bat-ca-si-chi-dan-nguoi-mau-an-tay-nguyen-do-truc-phuong-lien-quan-ma-tuy-185241114120254879.htm",
    "https://vnexpress.net/dien-vien-hai-bi-tam-giu-vi-lien-quan-ma-tuy-4475240.html",
    "https://thanhnien.vn/dj-thai-hoang-vua-bi-bat-vi-tang-tru-ma-tuy-la-ai-185230425153220627.htm",
    "https://thanhnien.vn/hang-loat-nghe-si-chau-a-va-viet-nam-dinh-nghi-an-dung-ma-tuy-185518486.htm",
    "https://vnexpress.net/nu-dj-trum-ma-tuy-nuoc-vui-o-tp-hcm-bi-truy-to-4847363.html",
]


class ArticleTextParser(HTMLParser):
    """Small HTML-to-text parser used when Crawl4AI is unavailable."""

    BLOCK_TAGS = {"article", "p", "br", "div", "section", "h1", "h2", "h3", "li"}
    SKIP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            text = html.unescape(data).strip()
            if text:
                self.parts.append(text)

    def text(self) -> str:
        raw = " ".join(self.parts)
        raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
        raw = re.sub(r"\n\s+", "\n", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def setup_directory() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def extract_title(page_html: str, fallback: str = "Unknown title") -> str:
    patterns = [
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']title["\'][^>]+content=["\']([^"\']+)["\']',
        r"<title[^>]*>(.*?)</title>",
        r"<h1[^>]*>(.*?)</h1>",
    ]
    for pattern in patterns:
        match = re.search(pattern, page_html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            title = re.sub(r"<[^>]+>", " ", match.group(1))
            title = html.unescape(re.sub(r"\s+", " ", title)).strip()
            if title:
                return title
    return fallback


def html_to_text(page_html: str) -> str:
    parser = ArticleTextParser()
    parser.feed(page_html)
    return parser.text()


async def crawl_with_crawl4ai(url: str) -> dict | None:
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        return None

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

    metadata = getattr(result, "metadata", {}) or {}
    markdown = getattr(result, "markdown", "") or ""
    title = metadata.get("title") or "Unknown title"
    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "source": urlparse(url).netloc,
        "content_markdown": markdown,
        "content_text": markdown,
        "crawler": "crawl4ai",
    }


def crawl_with_requests(url: str) -> dict:
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding

    title = extract_title(response.text)
    text = html_to_text(response.text)
    markdown = f"# {title}\n\nSource: {url}\n\n{text}\n"

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "source": urlparse(url).netloc,
        "content_markdown": markdown,
        "content_text": text,
        "crawler": "requests",
    }


async def crawl_article(url: str) -> dict:
    if os.getenv("USE_CRAWL4AI") == "1":
        try:
            article = await crawl_with_crawl4ai(url)
            if article and len(article.get("content_text", "")) > 500:
                return article
        except Exception:
            print("Crawl4AI failed, falling back to requests.")
    return crawl_with_requests(url)


async def crawl_all() -> None:
    setup_directory()

    for index, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{index}/{len(ARTICLE_URLS)}] Crawling: {url}")
        article = await crawl_article(url)
        filename = f"article_{index:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved: {filepath}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
