from functools import partial
from app.services.crawlers.base_crawler import BaseCrawler
from app.services.notifications import NotificationHub
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
from app.services.crawlers.telegram_crawler import TelegramCrawlerService
from app.services.notifications import notification_hub
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def _run_job(
    source_id: str,
    crawler_cls: type[BaseCrawler],
    notification_hub: NotificationHub
) -> None:
    async with AsyncSessionLocal() as db:
        service = crawler_cls(db, notification_hub)
        await service.crawl(source_id)


switcher = {
    SourceType.NEWS_SITE: partial(_run_job, crawler_cls=HtmlCrawlService, notification_hub=notification_hub),
    SourceType.RSS: partial(_run_job, crawler_cls=RssCrawlService, notification_hub=notification_hub),
    SourceType.TELEGRAM_CHANNEL: partial(_run_job, crawler_cls=TelegramCrawlerService, notification_hub=notification_hub),
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
        logger.error(
            f"Error running scheduled job for source {source_id}: {e}")
    return False
