from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging

import httpx
from sqlalchemy.exc import SQLAlchemyError 

logger = logging.getLogger(__name__)

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.article import Article
from app.models.crawl_job import CrawlJob
from app.models.keyword_hit import KeywordHit
from app.models.monitored_keyword import MonitoredKeyword
from app.models.source import Source
from app.models.status import Status
from app.scrapers.default import DefaultScraper
from app.services.crawlers.base_crawler import BaseCrawler
from app.services.es import elastic_service
from app.services.keyword_detector import detect_keywords, normalize_keyword
from app.services.notifications import notification_hub

class HtmlCrawlService (BaseCrawler):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def crawl(self, source_id: str) -> CrawlJob:
        """Runs the crawling process for a given source. This includes discovering article URLs, fetching article data, detecting keywords, and storing results in the database and search index."""
        source = await self.db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        job = CrawlJob(source_id=source.id, status=Status.RUNNING)
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        try:
            scraper = self._build_scraper(source)
            urls = await scraper.discover_article_urls()
            job.articles_found = len(urls)
            active_keywords = await self._get_keywords()
            created = 0

            for url in urls:
                existing = await self.db.scalar(select(Article).where(Article.url == url))
                if existing:
                    continue

                scraped = await scraper.fetch_article(url)
                if not scraped:
                    continue
                
                matched_keywords = detect_keywords(scraped.content_text, active_keywords)
                article = Article(
                    source_id=source.id,
                    external_id=scraped.external_id,
                    url=scraped.url,
                    title=scraped.title,
                    author=scraped.author,
                    published_at=scraped.published_at,
                    content_html=scraped.content_html,
                    content_text=scraped.content_text,
                    summary=scraped.summary,
                    language=scraped.language,
                    tags_csv=",".join(scraped.tags) if scraped.tags else None,
                    raw_payload_json=scraped.raw_payload_json,
                    checksum=scraped.checksum,
                    is_alert=bool(matched_keywords),
                    matched_keywords_csv=",".join(matched_keywords) if matched_keywords else None,
                )
                self.db.add(article)
                await self.db.flush()

                for keyword in matched_keywords:
                    self.db.add(KeywordHit(article_id=article.id, keyword=keyword))

                await self.db.commit()
                await self.db.refresh(article)
                created += 1

                await self._send_notification(article, source, matched_keywords)
                if matched_keywords:
                    await self._index_article(article,  matched_keywords)

            job.articles_created = created
            job.status = Status.COMPLETED
            job.finished_at = datetime.now(timezone.utc)
        except SQLAlchemyError as db_exc:
            logger.error(f"Database error during crawl job for source {source_id}: {db_exc}")
            job.status = Status.FAILED
            job.error_message = "Database error occurred during crawling."            
        except httpx.HTTPStatusError as http_exc:
            logger.error(f"HTTP error during crawl job for source {source_id}: {http_exc}")
            job.status = Status.FAILED
            job.error_message = f"HTTP error {http_exc.response.status_code} while crawling."
        except httpx.RequestError as req_exc:
            logger.error(f"Network error during crawl job for source {source_id}: {req_exc}")
            job.status = Status.FAILED
            job.error_message = "Network error occurred during crawling."
        except Exception as exc:
            logger.error(f"Unexpected error during crawl job for source {source_id}: {exc}")
            job.status = Status.FAILED
            job.error_message = str(exc)
        finally:
            job.finished_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(job)
            
        return job

    def _get_crawler_class(self):
        #TODO: implement source-specific scrapers and map them using the crawler_key field in the Source model. For now, we will use a default scraper for all sources.
        # crawler_cls = CRAWLERS.get(crawler_key)
        # if not crawler_cls:
        #     raise ValueError(f"Unsupported crawler key: {crawler_key}")
        return DefaultScraper  # crawler_cls

    def _build_scraper(self, source: Source):
        crawler_cls = self._get_crawler_class()
        return crawler_cls(source.base_url)
