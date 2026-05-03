from datetime import datetime
import hashlib

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.dto.rss_feed import RssFeed
from app.dto.scraped_article import ScrapedArticle
from app.utils.bot_challenge_detector import looks_like_bot_challenge
from app.utils.html_utils import extract_rss_content_html, html_to_text, get_content


class RssScraper:
    """Scraper for fetching articles from RSS feeds."""

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
            rss_html = extract_rss_content_html(
                item,
            )
            rss_text = html_to_text(rss_html) if rss_html else None

            feed = RssFeed(
                id=item.get("id", ""),
                url=item.get("link", ""),
                title=item.get("title", ""),
                author=item.get("author", None),
                published=(
                    datetime(*item.published_parsed[:6])
                    if item.get("published_parsed")
                    else None
                ),
                summary=item.get("summary", None),
                content_html=rss_html,
                content_text=rss_text,
                tags=[self._get_tag(tag) for tag in item.get("tags", [])],
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
            content_html, content_text = get_content(soup)

        except httpx.HTTPStatusError:
            if looks_like_bot_challenge(response.text):
                print(f"Bot challenge detected for URL: {feed.url}")
            content_html = feed.content_html
            content_text = feed.content_text.strip() if feed.content_text else None

        if not feed.title or not content_text:
            return None

        return ScrapedArticle(
            external_id=feed.id,
            url=feed.url,
            title=feed.title,
            author=feed.author,
            language="",
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
                "published": (feed.published.isoformat() if feed.published else None),
                "summary": feed.summary,
                "tags": feed.tags,
            },
            checksum=hashlib.sha256(content_text.encode("utf-8")).hexdigest(),
        )

    def _get_tag(self, tag) -> str:
        text = ""
        text = tag.get("label", "")
        if not text and tag.get("term"):
            text = tag["term"]
        return text.strip()
