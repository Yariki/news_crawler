from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.source import Source
from app.services.crawler import CrawlService

scheduler = AsyncIOScheduler(timezone="UTC")


async def refresh_scheduler_jobs() -> None:
    scheduler.remove_all_jobs()
    async with AsyncSessionLocal() as db:
        result = await db.scalars(select(Source).where(Source.is_enabled.is_(True)))
        for source in result.all():
            scheduler.add_job(
                _run_source_job,
                "interval",
                minutes=source.scrape_interval_minutes,
                id=f"source-{source.id}",
                replace_existing=True,
                args=[source.id],
            )


async def _run_source_job(source_id: int) -> None:
    async with AsyncSessionLocal() as db:
        service = CrawlService(db)
        await service.run_source(source_id)
