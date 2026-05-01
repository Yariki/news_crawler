from abc import ABC, abstractmethod
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models import MonitoredKeyword, CrawlJob, Source, Article
from app.services.keyword_detector import normalize_keyword


class BaseCrawler(ABC):

    def __init__(self, db: AsyncSession):
        self.db = db

    @abstractmethod
    async def crawl(self, source_id: str) -> CrawlJob | None:
        """Abstract method to be implemented by specific crawler types. This method should contain the logic for crawling a source, including discovering article URLs, fetching article data, detecting keywords, and storing results in the database and search index."""
        pass

    async def _get_keywords(self) -> list[str]:
        result = await self.db.scalars(
            select(MonitoredKeyword.keyword)
            .where(MonitoredKeyword.is_enabled.is_(True))
            .order_by(MonitoredKeyword.keyword)
        )
        keywords = [normalize_keyword(value) for value in result.all() if value]
        return keywords or settings.default_keywords_list

    async def _index_article(self, article: Article, source: Source, matched_words: list[str]):
        from app.services.es import elastic_service
        await elastic_service.index_article(
            {
                "article_id": article.id,
                "source_id": source.id,
                "source_name": source.name,
                "title": article.title,
                "content_text": article.content_text,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "url": article.url,
                "language": article.language,
                "is_alert": article.is_alert,
                "matched_keywords": matched_words,
            }
        )

    async def _send_notification(self, article: Article, matched_words: list[str]):
        from app.services.notifications import notification_hub
        await notification_hub.broadcast(
            "keywords_alert", {
                "article_id": article.id,
                "title": article.title,
                "url": article.url,
                "matched_keywords": matched_words,
                "published_at": article.published_at,
            }
        )
