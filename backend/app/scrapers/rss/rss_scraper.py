import feedparser
import httpx
import hashlib
from bs4 import BeautifulSoup
from app.dto.rss_feed import RssFeed
from app.dto.scraped_article import ScrapedArticle             


class RssScraper:
    """Scraper for fetching articles from RSS feeds."""
    def __init__(self, rss_url: str):
        self.rss_url = rss_url
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; NewsMonitorBot/0.1)"},
        )


    async def discover_rss_urls(self) -> list[RssFeed]:
        """Fetches the RSS feed URL and extracts feed items."""
        response_feeds = feedparser.parse(self.rss_url)
        feeds = list[RssFeed]
        for item in response_feeds.entries:
            feed = RssFeed(
                id=item.get("id", ""),
                url=item.get("link", ""),
                title=item.get("title", ""),
                author=item.get("author", None),
                published=item.get("published_parsed", None),
                summary=item.get("summary", None),
                tags=[tag.get("label", "") for tag in item.get("tags", [])],
                )
            feeds.append(feed)

        return feeds

    async def fetch_article(self, feed: RssFeed) -> ScrapedArticle:
        """Fetches the article URL from the RSS feed item and extracts structured data."""
        response = await self.client.get(feed.url)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        content_html, content_text = self._get_content(soup)

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
                "published": feed.published.isoformat() if feed.published else None,
                "summary": feed.summary,
                "tags": feed.tags,
            },
            checksum=hashlib.sha256(content_text.encode("utf-8")).hexdigest()
        )
        
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
