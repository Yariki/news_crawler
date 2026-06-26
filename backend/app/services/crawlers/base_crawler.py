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
from app.messaging.messages.job_update import JobUpdateMessage
from app.messaging.messages.keywords_match import KeywordsMatchMessage
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
from app.messaging.rabbitmq_client import RabbitMQClient
import logging

from app.services.robots import RobotsService

logger = logging.getLogger(__name__)


SCRAPPERS = {
    SourceType.NEWS_SITE: DefaultScraper,
    SourceType.RSS: RssScraper,
    SourceType.TELEGRAM_CHANNEL: TelegramScrapper
}

class BaseCrawler(ABC):
    """BaseCrawler is an abstract class that defines the structure and common functionality for different types of crawlers. It provides methods for crawling sources, detecting keywords, indexing articles, and sending notifications. Specific crawler implementations should inherit from this class and implement the crawl method with the logic specific to their source type."""
    def __init__(self, db: AsyncSession, rabbitmq_client: RabbitMQClient | None = None):
        self._db = db
        self._elasticsearch_client = ElasticService()
        self._rabbitmq_client = rabbitmq_client

    async def _get_keywords(self) -> list[str]:
        result = await self._db.scalars(
            select(MonitoredKeyword.keyword)
            .where(MonitoredKeyword.is_enabled.is_(True))
            .order_by(MonitoredKeyword.keyword)
        )
        keywords = [normalize_keyword(value)
                    for value in result.all() if value]
        return keywords or settings.default_keywords_list

    async def _index_article(self, article: Article, source: Source, matched_words: list[str]):
        if not self._elasticsearch_client:
            logger.warning("Elasticsearch client not configured, skipping indexing for article %s", article.id)
            return
        await self._elasticsearch_client.index_article(
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

    async def _send_matched_words_notification(self, article: Article, matched_words: list[str]):
        if not self._rabbitmq_client:
            logger.warning("RabbitMQ client not configured, skipping notification for article %s", article.id)
            return

        keywords_match_message = KeywordsMatchMessage(
            article_id=str(article.id),
            title=article.title,
            url=article.url,
            matched_keywords=matched_words,
            published_at=str(article.published_at.isoformat()) if article.published_at else None,
        )
        await self._rabbitmq_client.publish(keywords_match_message)


    async def _send_job_update(self, job: CrawlJob, articles_found: int | None = None, articles_created: int | None = None):
        if not self._rabbitmq_client:
            logger.warning("RabbitMQ client not configured, skipping job finished notification for job %s", job.id)
            return

        job_update_message = JobUpdateMessage(
            job_id=job.id,
            status=str(job.status),
            articles_found=articles_found if articles_found is not None else job.articles_found,
            articles_created=articles_created if articles_created is not None else job.articles_created,
            error_message=job.error_message if job.error_message else "",
            source_id=job.source_id if job.source_id else None,
            started_at=str(job.started_at.isoformat()),
            finished_at=str(job.finished_at.isoformat()) if job.finished_at else "",
        )
        await self._rabbitmq_client.publish(job_update_message)

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
        source = await SourceRepository(self._db).get_source_by_id(source_id)
        if not source:
            raise ValueError("Source not found")

        robots_service = RobotsService(source.base_url, self._db)
        await robots_service.fetch_robot()
        crawl_delay = robots_service.crawl_delay("*")

        keyword_rp = KeywordHitRepository(self._db)
        article_rp = ArticleRepository(self._db)
        crawl_rp = CrawlJobRepository(self._db)
        job = await crawl_rp.create_crawl_job(source_id, Status.RUNNING)

        await self._send_job_update(job, articles_found=0, articles_created=0)  # Initial job update

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

                await self._index_article_and_send_notification(source, matched_words, article)

                await self._update_job_info(crawl_rp, job, created)

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
            await self._send_job_update(job)

        return job

    async def _update_job_info(self, crawl_rp, job, created):
        if created % 5 != 0: # Update job info every 5 articles to reduce database writes
            return
        job.articles_created = created
        await crawl_rp.update_crawl_job(job)
        await self._send_job_update(job, articles_found=job.articles_found, articles_created=created)

    async def _index_article_and_send_notification(self, source, matched_words, article):
        await self._index_article(article, source, matched_words)
        if matched_words:
            await self._send_matched_words_notification(article, matched_words)
