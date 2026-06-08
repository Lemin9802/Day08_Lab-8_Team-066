"""
Task 2 — Crawl bài báo về nghệ sĩ liên quan tới ma tuý.

Yêu cầu:
    1. Crawl tối thiểu 5 bài báo từ các trang tin tức Việt Nam.
    2. Lưu output vào data/landing/news/
    3. Mỗi bài lưu 1 file JSON với metadata:
       url, title, date_crawled, content_markdown.

Ghi chú:
    Repo gợi ý Crawl4AI, nhưng ở đây dùng requests + BeautifulSoup
    để nhẹ hơn và dễ chạy trên Windows.
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


ARTICLE_URLS = [
    "https://dantri.com.vn/phap-luat/ca-si-long-nhat-cung-son-ngoc-minh-bi-bat-20260520122834562.htm",
    "https://vov.vn/giai-tri/nghe-si/rapper-binh-gold-vua-bi-bat-vi-duong-tinh-voi-ma-tuy-la-ai-post1217365.vov",
    "https://vnexpress.net/ca-si-miu-le-bi-bat-qua-tang-dung-ma-tuy-o-bai-bien-5072657.html",
    "https://soha.vn/xet-xu-dien-vien-hai-huu-tin-2023042810420088.htm",
    "https://nld.com.vn/cong-an-tp-hcm-ket-luan-vu-ca-si-chi-dan-dung-ma-tuy-196250821135822527.htm",
]


def clean_text(text: str) -> str:
    """Chuẩn hóa khoảng trắng."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_title(soup: BeautifulSoup) -> str:
    """Lấy title từ h1, og:title hoặc title tag."""
    h1 = soup.find("h1")
    if h1:
        h1_text = clean_text(h1.get_text(" ", strip=True))
        if h1_text:
            return h1_text

    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return clean_text(og_title["content"])

    title_tag = soup.find("title")
    if title_tag:
        title_text = clean_text(title_tag.get_text(" ", strip=True))
        if title_text:
            return title_text

    return "Unknown"


def extract_article_text(soup: BeautifulSoup) -> str:
    """
    Extract nội dung bài báo theo cách generic.
    Ưu tiên article/main/content container, sau đó fallback sang toàn bộ p tag.
    """
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    candidates = [
        soup.find("article"),
        soup.find("main"),
        soup.find("div", class_=re.compile("article|content|detail|body|news", re.I)),
        soup.find("div", id=re.compile("article|content|detail|body|news", re.I)),
    ]

    article_container = None
    for candidate in candidates:
        if candidate:
            article_container = candidate
            break

    if article_container:
        paragraphs = article_container.find_all("p")
    else:
        paragraphs = soup.find_all("p")

    lines = []
    seen = set()

    for p in paragraphs:
        text = clean_text(p.get_text(" ", strip=True))

        # Bỏ đoạn quá ngắn hoặc trùng
        if len(text) < 30:
            continue
        if text in seen:
            continue

        seen.add(text)
        lines.append(text)

    return "\n\n".join(lines)


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài báo và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str,
            "content_markdown": str
        }
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")

    title = extract_title(soup)
    content = extract_article_text(soup)

    content_markdown = f"# {title}\n\n"
    content_markdown += f"**Source:** {url}\n\n"
    content_markdown += f"**Crawled:** {datetime.now().isoformat()}\n\n"
    content_markdown += "---\n\n"
    content_markdown += content

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": content_markdown,
    }


async def crawl_all():
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    setup_directory()

    if len(ARTICLE_URLS) < 5:
        raise ValueError("Task 2 yêu cầu tối thiểu 5 bài báo.")

    success_count = 0

    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")

        try:
            article = await crawl_article(url)

            filename = f"article_{i:02d}.json"
            filepath = DATA_DIR / filename

            filepath.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            content_len = len(article.get("content_markdown", ""))
            print(f"  ✓ Saved: {filepath} ({content_len} chars)")

            if content_len < 500:
                print("  ⚠ Nội dung hơi ngắn, nên mở file JSON kiểm tra lại.")

            success_count += 1

        except Exception as exc:
            print(f"  ✗ Failed: {url}")
            print(f"    Error: {exc}")

    print("=" * 60)
    print(f"Done. Crawled successfully: {success_count}/{len(ARTICLE_URLS)} articles")
    print(f"Output directory: {DATA_DIR}")

    if success_count < 5:
        raise RuntimeError("Chưa crawl đủ 5 bài. Cần thay URL lỗi hoặc xử lý lại.")


if __name__ == "__main__":
    asyncio.run(crawl_all())