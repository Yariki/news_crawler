from app.models import CrawlJob
from app.services.crawlers.base_crawler import BaseCrawler
import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RssCrawlService(BaseCrawler):
    """Service class responsible for crawling RSS feed sources. It implements the crawl method defined in the BaseCrawler abstract class, which includes discovering article URLs from the RSS feed, fetching article data, detecting keywords, and storing results in the database and search index."""

    def __init__(self, db: AsyncSession):
        """Initializes the RssCrawlService with a database session."""
        super().__init__(db)

    async def crawl(self, source_id: str) -> CrawlJob | None:
        return await super().crawl(source_id)

