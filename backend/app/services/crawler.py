from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.article import Article
from app.models.crawl_job import CrawlJob
from app.models.keyword_hit import KeywordHit
from app.models.monitored_keyword import MonitoredKeyword
from app.models.source import Source
from app.services.es import elastic_service
from app.services.keyword_detector import detect_keywords, normalize_keyword
from app.services.notifications import notification_hub


# TODO: implement source-specific scrapers and map them using the crawler_key field in the Source model. For now, we will use a default scraper for all sources.
# CRAWLERS = {
#     "news1": TimesScraper,
#     "news2": RIAScraper,
# }


class CrawlService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_sources(self) -> list[Source]:
        result = await self.db.scalars(select(Source).order_by(Source.id))
        return list(result.all())

    async def create_source(self, payload) -> Source:
        source = Source(
            name=payload.name,
            base_url=str(payload.base_url),
            language=payload.language,
            source_type=payload.source_type,
            crawler_key=payload.crawler_key,
            scrape_interval_minutes=payload.scrape_interval_minutes,
            is_enabled=payload.is_enabled,
        )
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def list_jobs(self, limit: int = 50) -> list[CrawlJob]:
        result = await self.db.scalars(select(CrawlJob).order_by(desc(CrawlJob.started_at)).limit(limit))
        return list(result.all())

    async def list_keywords(self) -> list[MonitoredKeyword]:
        result = await self.db.scalars(select(MonitoredKeyword).order_by(MonitoredKeyword.keyword))
        return list(result.all())

    async def create_keyword(self, keyword: str) -> MonitoredKeyword:
        normalized = normalize_keyword(keyword)
        existing = await self.db.scalar(select(MonitoredKeyword).where(MonitoredKeyword.keyword == normalized))
        if existing:
            return existing
        item = MonitoredKeyword(keyword=normalized, is_enabled=True)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete_keyword(self, keyword_id: int) -> None:
        item = await self.db.get(MonitoredKeyword, keyword_id)
        if item is None:
            return
        await self.db.delete(item)
        await self.db.commit()

    async def dashboard_stats(self) -> dict:
        return {
            "sources_total": await self.db.scalar(select(func.count(Source.id))) or 0,
            "sources_enabled": await self.db.scalar(select(func.count(Source.id)).where(Source.is_enabled.is_(True))) or 0,
            "articles_total": await self.db.scalar(select(func.count(Article.id))) or 0,
            "alerts_total": await self.db.scalar(select(func.count(Article.id)).where(Article.is_alert.is_(True))) or 0,
            "jobs_total": await self.db.scalar(select(func.count(CrawlJob.id))) or 0,
            "keywords_total": await self.db.scalar(select(func.count(MonitoredKeyword.id)).where(MonitoredKeyword.is_enabled.is_(True))) or 0,
            "elasticsearch_document_count": await elastic_service.count(),
        }

    async def get_active_keywords(self) -> list[str]:
        result = await self.db.scalars(
            select(MonitoredKeyword.keyword)
            .where(MonitoredKeyword.is_enabled.is_(True))
            .order_by(MonitoredKeyword.keyword)
        )
        keywords = [normalize_keyword(value) for value in result.all() if value]
        return keywords or settings.default_keywords_list

    async def run_source(self, source_id: int) -> CrawlJob:
        source = await self.db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        job = CrawlJob(source_id=source.id, status="running")
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        try:
            scraper = self._build_scraper(source)
            urls = await asyncio.to_thread(scraper.discover_article_urls)
            job.articles_found = len(urls)
            active_keywords = await self.get_active_keywords()
            created = 0

            for url in urls:
                existing = await self.db.scalar(select(Article).where(Article.url == url))
                if existing:
                    continue

                scraped = await asyncio.to_thread(scraper.fetch_article, url)
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
                        "matched_keywords": matched_keywords,
                    }
                )
                created += 1

                if matched_keywords:
                    await notification_hub.broadcast(
                        "keyword_alert",
                        {
                            "article_id": article.id,
                            "title": article.title,
                            "url": article.url,
                            "matched_keywords": matched_keywords,
                            "published_at": article.published_at.isoformat() if article.published_at else None,
                        },
                    )

            job.articles_created = created
            job.status = "completed"
            job.finished_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(job)
            return job
        except Exception as exc:
            job.status = "failed"
            job.finished_at = datetime.now(timezone.utc)
            job.error_message = str(exc)
            await self.db.commit()
            await self.db.refresh(job)
            raise

    def _get_crawler_class(self):
        #TODO: implement source-specific scrapers and map them using the crawler_key field in the Source model. For now, we will use a default scraper for all sources.
        # crawler_cls = CRAWLERS.get(crawler_key)
        # if not crawler_cls:
        #     raise ValueError(f"Unsupported crawler key: {crawler_key}")
        return DefaultScraper  # crawler_cls

    def _build_scraper(self, source: Source):
        crawler_cls = self._get_crawler_class()
        return crawler_cls(source.base_url)
