from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import Source
from app.models.source import Source
from app.models.source_type import SourceType
from app.services.crawler import CrawlService
from app.services.rss_crawler import RssCrawler

scheduler = AsyncIOScheduler(timezone="UTC")

async def _run_source_job(source_id: int) -> None:
    async with AsyncSessionLocal() as db:
        service = CrawlService(db)
        await service.run_source(source_id)

async def _run_rss_job(source_id: int) -> None:
    async with AsyncSessionLocal() as db:
        service = RssCrawler(db)
        await service.crawl(source_id)

switcher = {
    SourceType.NEWS_SITE: _run_source_job,
    SourceType.RSS: _run_rss_job,
}

async def refresh_scheduler_jobs() -> None:
    scheduler.remove_all_jobs()
    async with AsyncSessionLocal() as db:
        result = await db.scalars(select(Source).where(Source.is_enabled.is_(True)))
        for source in result.all():
            handler = switcher.get(source.source_type)
            if not handler:
                continue

            scheduler.add_job(
                handler,
                "interval",
                minutes=source.scrape_interval_minutes,
                id=f"source-{source.id}",
                replace_existing=True,
                args=[source.id],
            )
