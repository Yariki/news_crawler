from abc import ABC

import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from app.core.const import ARTICLE_LINK_RE, LINK_RE, PATTERNS
from app.dto.scraped_article import ScrapedArticle


class BaseScraper(ABC):
    """Base class for all scrapers. Defines the interface and common utilities."""
    def __init__(self, url):
        self.base_url = url
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; NewsMonitorBot/0.1)"},
        )

    async def discover_article_urls(self) -> list[str]:
        """Fetches the base URL and extracts article URLs using a regex pattern."""
        response = await self.client.get(self.base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        found: list[str] = []
        seen: set[str] = set()
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "").strip()
            if not href:
                continue
            full_url = urljoin(self.base_url, href)
            print(f"Discovered URL: {full_url}; {any(pattern.search(full_url) for pattern in PATTERNS)}")
            if any(pattern.search(full_url) for pattern in PATTERNS) and full_url not in seen:
                seen.add(full_url)
                found.append(full_url)

        return found

    async def fetch_article(self, url: str) -> ScrapedArticle | None:
        """Fetches the article URL and extracts structured data. This method should be overridden by subclasses for site-specific parsing logic."""
        response = await self.client.get(url)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        title = self._get_title(soup)
        published_at = self._get_published_at(soup)
        author = self._get_author(soup)
        content_html, content_text = self._get_content(soup)
        summary = self._build_summary(content_text)
        tags = self._get_tags(soup)
        external_id = self._extract_external_id(url)
        checksum = hashlib.sha256(content_text.encode("utf-8")).hexdigest()

        if not title or not content_text:
            return None


        return ScrapedArticle(
            external_id=external_id,
            url=url,
            title=title,
            author=author,
            published_at=published_at,
            content_html=content_html,
            content_text=content_text,
            summary=summary,
            language="ru",
            tags=tags,
            raw_payload_json={
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "url": url,
                "title": title,
                "author": author,
                "published_at": published_at.isoformat() if published_at else None,
                "tags": tags,
            },
            checksum=checksum,
        )

    def _get_title(self, soup: BeautifulSoup) -> str:
        """Extracts the title of the article from the HTML soup."""
        for selector in ["meta[property='og:title']", "meta[property='title']", "title", "h1",]:
            if selector.startswith("meta"):
                node = soup.select_one(selector)
                if node and node.get("content"):
                    return node["content"].strip()
            else:
                node = soup.select_one(selector)
                if node and node.get_text(strip=True):
                    return node.get_text(strip=True)
        return "Untitled"

    def _get_published_at(self, soup: BeautifulSoup) -> datetime | None:
        for selector in ["meta[property='article:published_time']", "time[datetime]"]:
            node = soup.select_one(selector)
            if node:
                dt = node.get("content") or node.get("datetime")
                if dt:
                    try:
                        return date_parser.parse(dt.replace("Z", "+00:00"))
                    except Exception:
                        pass
        return None

    def _get_author(self, soup: BeautifulSoup) -> str | None:
        for selector in ["meta[name='author']", "meta[property='article:author']", ".author", "author"]:
            node = soup.select_one(selector)
            if node:
                if selector.startswith("meta"):
                    if node.get("content"):
                        return node["content"].strip()
                else:
                    if node.get_text(strip=True):
                        return node.get_text(strip=True)
        return None

    def _get_content(self, soup: BeautifulSoup) -> tuple[str | None, str]:
        for container_selector in ["article", "main", "body"]:
            container = soup.select_one(container_selector)
            if not container:
                continue
            paragraphs = [p.get_text(" ", strip=True)
                          for p in container.select("p")]
            paragraphs = [p for p in paragraphs if len(p) > 40]
            if paragraphs:
                html = "\n".join(str(p) for p in container.select("p"))
                text = "\n\n".join(paragraphs)
                return html, text
        return None, soup.get_text(" ", strip=True)

    def _build_summary(self, text: str) -> str | None:
        compact = " ".join(text.split())
        return compact[:300] + ("..." if len(compact) > 300 else "") if compact else None

    def _get_tags(self, soup: BeautifulSoup) -> list[str]:
        tags: list[str] = []
        for selector in ["meta[property='article:tag']", ".tags a", ".tag", "a[href*='/tag/']"]:
            for node in soup.select(selector):
                if selector.startswith("meta"):
                    if node.get("content"):
                        tags.append(node["content"].strip())
                else:
                    if node.get_text(strip=True):
                        tags.append(node.get_text(strip=True))
        return list(dict.fromkeys(tags))[:10]

    def _extract_external_id(self, url: str) -> str:
        match = re.search(r"-a(\d+)$", url.rstrip("/"))
        return match.group(1) if match else url.rstrip("/").split("/")[-1]
