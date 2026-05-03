from __future__ import annotations
from datetime import datetime, timedelta, timezone
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.source import Source
from app.models.source_type import SourceType
from app.services.crawlers.html_crawler import HtmlCrawlService
from app.services.crawlers.rss_crawler import RssCrawlService

scheduler = AsyncIOScheduler(timezone="UTC")


async def _run_source_job(source_id: str) -> None:
    async with AsyncSessionLocal() as db:
        service = HtmlCrawlService(db)
        await service.crawl(source_id)


async def _run_rss_job(source_id: int) -> None:
    async with AsyncSessionLocal() as db:
        service = RssCrawlService(db)
        await service.crawl(source_id)


switcher = {
    SourceType.NEWS_SITE: _run_source_job,
    SourceType.RSS: _run_rss_job,
}


async def refresh_scheduler_jobs() -> None:
    scheduler.remove_all_jobs()

    if settings.app_mode == "dev":
        logging.getLogger("apscheduler").setLevel(logging.DEBUG)

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


async def run_scheduled_job(source_id: str) -> bool:
    try:
        job = scheduler.get_job(f"source-{source_id}")
        if job:
            job.modify(next_run_time=datetime.now(timezone.utc))
            return True
    except Exception as e:
        print(f"Error running scheduled job for source {source_id}: {e}")
    return False
