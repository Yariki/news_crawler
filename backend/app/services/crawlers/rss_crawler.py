import asyncio
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.models import CrawlJob, Source, Article, KeywordHit
from app.models.status import Status
from app.scrapers.rss.rss_scraper import RssScraper
from app.services.crawlers.base_crawler import BaseCrawler
from app.services.es import elastic_service
from app.services.keyword_detector import detect_keywords
from app.services.notifications import notification_hub


class RssCrawlService(BaseCrawler):
    """Service class responsible for crawling RSS feed sources. It implements the crawl method defined in the BaseCrawler abstract class, which includes discovering article URLs from the RSS feed, fetching article data, detecting keywords, and storing results in the database and search index."""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def crawl(self, source_id: str) -> CrawlJob |  None:
        """ Runs the crawling process for a given RSS source. This includes discovering article URLs, fetching article data, detecting keywords, and storing results in the database and search index."""
        source = await self.db.get(Source, source_id)
        if not source:
            raise ValueError("Source not found")

        job = CrawlJob(source_id=source_id, status=Status.RUNNING)
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        try:
            scraper = RssScraper(source.url)
            urls = await scraper.discover_rss_urls()
            job.articles_found = len(urls)
            active_keywords = await self._get_keywords()
            created = 0

            for url in urls:
                exists = await self.db.scalar(select(Article).where(Article.url == url))
                if exists:
                    continue

                article_data = await scraper.fetch_article(url)
                if not article_data:
                    continue

                matched_words = detect_keywords(article_data.content_text, active_keywords)
                article = Article(
                    source_id=source_id,
                    external_id=article_data.id,
                    url=url,
                    title=article_data.title,
                    author=article_data.author,
                    published_at=article_data.published_at,
                    content_html=article_data.content_html,
                    content_text=article_data.content_text,
                    summary=article_data.summary,
                    language=article_data.language,
                    tags_csv=",".join(article_data.tags_csv) if article_data.tags_csv else None,
                    raw_payload_json=article_data.raw_payload_json,
                    checksum=article_data.checksum,
                    is_alert=bool(matched_words),
                    matched_keywords_csv=",".join(matched_words) if matched_words else None,
                )

                self.db.add(article)
                await self.db.flush()

                for keyword in matched_words:
                    self.db.add(KeywordHit(article_id=article.id, keyword=keyword.strip()))

                await self.db.commit()
                await self.db.refresh(article)
                created += 1

                await self._index_article(article, source, matched_words)
                if matched_words:
                    await self._send_notification(article, matched_words)

            job.articles_created = created
            job.status = Status.COMPLETED

        except httpx.HTTPStatusError as ex:
            job.status = Status.FAILED
            job.error_message = f"HTTP error {ex.response.status_code}: {ex.request.url}"
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