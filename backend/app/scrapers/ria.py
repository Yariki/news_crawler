import re
from datetime import datetime
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup


ARTICLE_URL_PATTERN = re.compile(r"^/(\d{8})/.*\.html$")


class RIAScraper:
    
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; NewsMonitorBot/0.1)"},
        )



    async def fetch_homepage(self) -> str:
        resp = await self.client.get(BASE_URL)
        resp.raise_for_status()
        return resp.text

    async def extract_article_links(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if ARTICLE_URL_PATTERN.match(href):
                if not href.startswith("http"):
                    href = BASE_URL + href
                links.add(href)

        return list(links)

    async def fetch_article(self, url: str) -> Optional[dict]:
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
        except Exception:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Title
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else None

        # Published date
        published_at = None
        time_tag = soup.find("time")
        if time_tag:
            dt = time_tag.get("datetime")
            if dt:
                try:
                    published_at = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                except Exception:
                    pass

        # Author
        author = None
        author_tag = soup.find(attrs={"class": "article__author"})
        if author_tag:
            author = author_tag.get_text(strip=True)

        # Content
        content_blocks = soup.find_all("div", attrs={"class": "article__text"})
        paragraphs = []

        for block in content_blocks:
            for p in block.find_all("p"):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)

        content_text = "\n".join(paragraphs)

        # Tags
        tags = []
        tag_elements = soup.find_all("a", href=True)
        for t in tag_elements:
            if "/tag/" in t["href"]:
                tags.append(t.get_text(strip=True))

        # External ID
        external_id = self.extract_external_id(url)

        if not title or not content_text:
            return None

        return {
            "url": url,
            "external_id": external_id,
            "title": title,
            "author": author,
            "published_at": published_at,
            "content_text": content_text,
            "tags": list(set(tags)),
        }

    def extract_external_id(self, url: str) -> str:
        # example: /20260406/iran-2085500793.html
        match = re.search(r"-(\d+)\.html$", url)
        return match.group(1) if match else url

    async def run(self) -> List[dict]:
        html = await self.fetch_homepage()
        links = await self.extract_article_links(html)

        articles = []
        for url in links:
            article = await self.fetch_article(url)
            if article:
                articles.append(article)

        return articles

    async def close(self):
        await self.client.aclose()