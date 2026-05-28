import asyncio
from datetime import datetime, timezone
from abc import ABC, abstractmethod

import httpx
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models import MonitoredKeyword, CrawlJob, Source, Article, KeywordHit
from app.models.source_type import SourceType
from app.models.status import Status
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.default import DefaultScraper
from app.scrapers.rss.rss_scraper import RssScraper
from app.scrapers.telegram.telegram_scraper import TelegramScrapper
from app.services.keyword_detector import normalize_keyword, detect_keywords
import logging

from app.services.robots import RobotsService

logger = logging.getLogger(__name__)



SCRAPPERS = {
    SourceType.NEWS_SITE: DefaultScraper,
    SourceType.RSS: RssScraper,
    SourceType.TELEGRAM_CHANNEL: TelegramScrapper
}

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
        keywords = [normalize_keyword(value)
                    for value in result.all() if value]
        return keywords or settings.default_keywords_list

    async def _index_article(self, article: Article, source: Source, matched_words: list[str]):
        from app.services.es import elastic_service
        await elastic_service.index_article(
            {
                "article_id": str(article.id),
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
                "article_id": str(article.id),
                "title": article.title,
                "url": article.url,
                "matched_keywords": matched_words,
                "published_at": str(article.published_at),
            }
        )

    def __get_crawler_class(self, source_type: SourceType = SourceType.UNKNOWN):

        crawler_cls = SCRAPPERS.get(source_type or SourceType.NEWS_SITE)
        if not crawler_cls:
            raise ValueError(f"Unsupported crawler key: {source_type}")
        return crawler_cls

    def _build_scraper(self, source: Source) -> BaseScraper:
        crawler_cls = self.__get_crawler_class(source.source_type)
        if not crawler_cls:
            raise ValueError(f"Invalid crawler class for source type {source.source_type}")
        return crawler_cls(source.base_url)

    async def crawl(self, source_id: str) -> CrawlJob:
        """Runs the crawling process for a given RSS source. This includes discovering article URLs, fetching article data, detecting keywords, and storing results in the database and search index."""
        source = await self.db.get(Source, source_id)
        if not source:
            raise ValueError("Source not found")

        robots_service = RobotsService(source.base_url, self.db)
        await robots_service.fetch_robot()
        crawl_delay = robots_service.crawl_delay("*")

        job = CrawlJob(source_id=source_id, status=Status.RUNNING)
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        try:
            scraper = self._build_scraper(source)
            feeds = await scraper.discover_urls()
            job.articles_found = len(feeds)
            active_keywords = await self._get_keywords()
            created = 0
            urls = [feed.url for feed in feeds if feed.url]
            existing_urls = set(await self.db.scalars(select(Article.url).where(Article.url.in_(urls))))

            for feed in feeds:
                if feed.url in existing_urls:
                    continue

                article_data = await scraper.fetch_article(feed)
                if not article_data:
                    continue

                matched_words = detect_keywords(
                    article_data.content_text, active_keywords
                )
                article = Article(
                    source_id=source_id,
                    external_id=article_data.external_id,
                    url=feed.url,
                    title=article_data.title,
                    author=article_data.author,
                    published_at=article_data.published_at,
                    fetched_at=datetime.now(timezone.utc),
                    content_html=article_data.content_html,
                    content_text=article_data.content_text,
                    summary=article_data.summary,
                    language=article_data.language,
                    tags_csv=(
                        ",".join(article_data.tags) if article_data.tags else None
                    ),
                    raw_payload_json=article_data.raw_payload_json,
                    checksum=article_data.checksum,
                    is_alert=bool(matched_words),
                    matched_keywords_csv=(
                        ",".join(matched_words) if matched_words else None
                    ),
                )

                self.db.add(article)
                await self.db.flush()

                for keyword in matched_words:
                    self.db.add(
                        KeywordHit(article_id=article.id, keyword=keyword.strip())
                    )

                await self.db.commit()
                await self.db.refresh(article)
                created += 1

                await self._index_article(article, source, matched_words)
                if matched_words:
                    await self._send_notification(article, matched_words)

                if crawl_delay:
                    logger.debug(f"Sleeping for {crawl_delay} seconds to respect crawl delay")
                    await asyncio.sleep(crawl_delay)

            job.articles_created = created
            job.status = Status.COMPLETED

        except httpx.HTTPStatusError as ex:
            job.status = Status.FAILED
            job.error_message = (
                f"HTTP error {ex.response.status_code}: {ex.request.url}"
            )
            logger.error("HTTP error crawling source %s: %s", source_id, ex)
        except httpx.RequestError as ex:
            job.status = Status.FAILED
            job.error_message = f"Network error: {ex}"
            logger.error("Network error crawling source %s: %s", source_id, ex)
        except SQLAlchemyError as ex:
            job.status = Status.FAILED
            job.error_message = f"Database error: {ex}"
            logger.error("Database error crawling source %s: %s", source_id, ex)
        except Exception as ex:
            job.status = Status.FAILED
            job.error_message = f"Unexpected error: {ex}"
            logger.exception("Unexpected error crawling source %s", source_id)
        finally:
            job.finished_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(job)

        return job
