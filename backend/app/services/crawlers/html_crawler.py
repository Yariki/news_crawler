from __future__ import annotations

from app.models import CrawlJob
from app.services.crawlers.base_crawler import BaseCrawler
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class HtmlCrawlService (BaseCrawler):
    """Service class responsible for crawling HTML page sources. It implements the crawl method defined in the BaseCrawler abstract class, which includes discovering article URLs from the HTML page, fetching article data, detecting keywords, and storing results in the database and search index."""

    def __init__(self, db: AsyncSession) -> None:
        """Initializes the HtmlCrawlService with a database session."""
        super().__init__(db)
