import asyncio
from dataclasses import asdict
from dataclasses import asdict
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import uuid
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.messaging.messages.base import MessageTypes
from app.models import MonitoredKeyword, CrawlJob, Source, Article, KeywordHit
from app.models.source_type import SourceType
from app.models.status import Status
from app.repositories.article_repository import ArticleRepository
from app.repositories.crawljob_repository import CrawlJobRepository
from app.repositories.keyword_hit_repository import KeywordHitRepository
from app.repositories.source_repository import SourceRepository
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.default import DefaultScraper
from app.scrapers.rss.rss_scraper import RssScraper
from app.scrapers.telegram.telegram_scraper import TelegramScrapper
from app.services.es import ElasticService
from app.services.keyword_detector import normalize_keyword, detect_keywords
import logging

from app.services.notifications import NotificationHub
from app.services.robots import RobotsService

logger = logging.getLogger(__name__)



SCRAPPERS = {
    SourceType.NEWS_SITE: DefaultScraper,
    SourceType.RSS: RssScraper,
    SourceType.TELEGRAM_CHANNEL: TelegramScrapper
}

class BaseCrawler(ABC):
    """BaseCrawler is an abstract class that defines the structure and common functionality for different types of crawlers. It provides methods for crawling sources, detecting keywords, indexing articles, and sending notifications. Specific crawler implementations should inherit from this class and implement the crawl method with the logic specific to their source type."""
    def __init__(self, db: AsyncSession, notification_hub: NotificationHub = None):
        self.db = db
        self.notification_hub = notification_hub
        self.elasticsearch_client = ElasticService()

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
        if not self.elasticsearch_client:
            logger.warning("Elasticsearch client not configured, skipping indexing for article %s", article.id)
            return
        await self.elasticsearch_client.index_article(
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
        if not self.notification_hub:
            logger.warning("NotificationHub not configured, skipping notification for article %s", article.id)
            return

        await self.notification_hub.broadcast(
            "keywords_alert", {
                "article_id": str(article.id),
                "title": article.title,
                "url": article.url,
                "matched_keywords": matched_words,
                "published_at": str(article.published_at),
            }
        )

    async def _send_job_finished(self, job: CrawlJob):
        if not self.notification_hub:
            logger.warning("NotificationHub not configured, skipping job finished notification for job %s", job.id)
            return

        await self.notification_hub.broadcast(
            "job_finished", {
                "job_id": str(job.id),
                "source_id": str(job.source_id),
                "status": job.status,
                "articles_found": job.articles_found,
                "articles_created": job.articles_created,
                "error_message": job.error_message,
                "started_at": str(job.started_at),
                "finished_at": str(job.finished_at) if job.finished_at else None,
            })

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

    async def crawl(self, source_id: str, use_delay: bool = True) -> CrawlJob:
        """Runs the crawling process for a given RSS source. This includes discovering article URLs, fetching article data, detecting keywords, and storing results in the database and search index."""
        source = await SourceRepository(self.db).get_source_by_id(source_id)
        if not source:
            raise ValueError("Source not found")

        robots_service = RobotsService(source.base_url, self.db)
        await robots_service.fetch_robot()
        crawl_delay = robots_service.crawl_delay("*")

        keyword_rp = KeywordHitRepository(self.db)
        article_rp = ArticleRepository(self.db)
        crawl_rp = CrawlJobRepository(self.db)
        job = await crawl_rp.create_crawl_job(source_id, Status.RUNNING)

        try:
            scraper = self._build_scraper(source)
            feeds = await scraper.discover_urls()
            job.articles_found = len(feeds)
            active_keywords = await self._get_keywords()
            created = 0
            urls = [feed.url for feed in feeds if feed.url]
            existing_urls = set(await article_rp.get_articles_urls(urls))

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

                await article_rp.add_article(article)

                for keyword in matched_words:
                    await keyword_rp.create_keyword_hit(KeywordHit(article_id=article.id, keyword=keyword.strip()))

                created += 1

                await self._index_article(article, source, matched_words)
                if matched_words:
                    await self._send_notification(article, matched_words)

                if use_delay and crawl_delay:
                    logger.debug(f"Sleeping for {crawl_delay} seconds to respect crawl delay")
                    await asyncio.sleep(crawl_delay)

            job.articles_created = created
            job.status = Status.COMPLETED
            job.finished_at = datetime.now(timezone.utc)
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
            await crawl_rp.update_crawl_job(job)
            await self._send_job_finished(job)

        return job
