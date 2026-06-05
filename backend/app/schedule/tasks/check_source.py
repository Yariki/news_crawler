
from functools import partial
import logging

from executing import Source
from sqlalchemy import select

from ...db.session import AsyncSessionLocal
from ...models.source_type import SourceType
from ...services.crawlers.base_crawler import BaseCrawler
from ...services.crawlers.html_crawler import HtmlCrawlService
from ...services.crawlers.rss_crawler import RssCrawlService
from ...services.crawlers.telegram_crawler import TelegramCrawlerService
from ...services.notifications import NotificationHub
from ...services.notifications import notification_hub

from ..celery_app import celery_app

logger = logging.getLogger(__name__)

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

@celery_app.task(name="schedule.tasks.run_scheduled_job")
async def run_scheduled_job(source_id: str):
    try:
        async with AsyncSessionLocal() as db:
            source = await db.scalar(select(Source).where(Source.id == source_id).where(Source.is_enabled.is_(True)))
            if not source:
                logger.warning(f"Source with id {source_id} not found")
                return False
            handler = switcher.get(source.source_type)
            if not handler:
                logger.warning(f"No handler for source type {source.source_type}")
                return False

            await handler(source_id=source_id)
    except Exception as e:
        logger.error(f"Error running scheduled job for source {source_id}: {e}")
