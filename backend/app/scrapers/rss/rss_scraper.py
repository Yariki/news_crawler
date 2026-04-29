from datetime import datetime
import hashlib

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.dto.rss_feed import RssFeed
from app.dto.scraped_article import ScrapedArticle

ARTICLE_CHARACTERS_NUMBER = 40


class RssScraper:
    """Scraper for fetching articles from RSS feeds."""

    CHALLENGE_MARKERS = (
        "please enable js",
        "please enable javascript",
        "disable any ad blocker",
        "attention required",
        "cf-browser-verification",
        "cloudflare",
        "datadome",
        "just a moment...",
    )

    def __init__(self, rss_url: str):
        self.rss_url = rss_url
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; NewsMonitorBot/0.1)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

    async def discover_rss_urls(self) -> list[RssFeed]:
        """Fetches the RSS feed URL and extracts feed items."""
        response_feeds = feedparser.parse(self.rss_url)
        feeds: list[RssFeed] = []

        for item in response_feeds.entries:
            rss_html = self._extract_rss_content_html(item)
            rss_text = self._html_to_text(rss_html) if rss_html else None

            feed = RssFeed(
                id=item.get("id", ""),
                url=item.get("link", ""),
                title=item.get("title", ""),
                author=item.get("author", None),
                published=item.get("published_parsed", None),
                summary=item.get("summary", None),
                content_html=rss_html,
                content_text=rss_text,
                tags=[tag.get("label", "") for tag in item.get("tags", [])],
                checksum=None,
            )
            feeds.append(feed)

        return feeds

    async def fetch_article(self, feed: RssFeed) -> ScrapedArticle | None:
        """Build article from RSS content first, then fallback to article URL."""
        content_html = None
        content_text = None

        response = await self.client.get(feed.url)
        try:
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            content_html, content_text = self._get_content(soup)

        except httpx.HTTPStatusError:
            if self._looks_like_bot_challenge(response.text):
                print(f"Bot challenge detected for URL: {feed.url}")
            content_html = feed.content_html
            content_text = feed.content_text.strip()

        if not feed.title or not content_text:
            return None

        return ScrapedArticle(
            external_id=feed.id,
            url=feed.url,
            title=feed.title,
            author=feed.author,
            language=None,
            published_at=feed.published,
            content_html=content_html,
            content_text=content_text,
            summary=feed.summary,
            tags=feed.tags,
            raw_payload_json={
                "id": feed.id,
                "url": feed.url,
                "title": feed.title,
                "author": feed.author,
                "published": datetime(*feed.published[:6]).isoformat() if feed.published else None,
                "summary": feed.summary,
                "tags": feed.tags,
            },
            checksum=hashlib.sha256(content_text.encode("utf-8")).hexdigest(),
        )

    def _extract_rss_content_html(self, item: dict) -> str | None:
        """Extract rich HTML body from RSS/Atom entry if available."""
        content_blocks = item.get("content") or []
        for block in content_blocks:
            value = block.get("value")
            if value and len(value.strip()) > ARTICLE_CHARACTERS_NUMBER:
                return value

        summary = item.get("summary")
        if summary and len(summary.strip()) > ARTICLE_CHARACTERS_NUMBER:
            return summary

        return None

    def _html_to_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)
        return " ".join(text.split())

    def _looks_like_bot_challenge(self, html: str) -> bool:
        text = html.lower()
        return any(marker in text for marker in self.CHALLENGE_MARKERS)

    def _get_content(self, soup: BeautifulSoup) -> tuple[str | None, str]:
        for container_selector in ["article", "main", "body"]:
            container = soup.select_one(container_selector)
            if not container:
                continue

            paragraphs = [p.get_text(" ", strip=True) for p in container.select("p")]
            paragraphs = [p for p in paragraphs if len(p) > 40]

            if paragraphs:
                html = "\n".join(str(p) for p in container.select("p"))
                text = "\n\n".join(paragraphs)
                return html, text

        return None, soup.get_text(" ", strip=True)