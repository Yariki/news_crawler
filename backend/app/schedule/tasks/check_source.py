
import asyncio
from functools import partial
import logging
from uuid import UUID
from sqlalchemy import select

from ...messaging.rabbitmq_client import RabbitMQClient

from ...models.source import Source

from ...db.session import AsyncSessionLocal
from ...models.source_type import SourceType
from ...services.crawlers.base_crawler import BaseCrawler
from ...services.crawlers.fake_crawler import FakeCrawlerService
from ...services.crawlers.html_crawler import HtmlCrawlService
from ...services.crawlers.rss_crawler import RssCrawlService
from ...services.crawlers.telegram_crawler import TelegramCrawlerService
from ...messaging.rabbitmq_client import get_rabbitmq_client

from ..celery_app import celery_app

logger = logging.getLogger(__name__)

_worker_loop = None

async def _run_job(
    source_id: str,
    crawler_cls: type[BaseCrawler]
) -> None:
    async with AsyncSessionLocal() as db:
        rabbitmq_client = await get_rabbitmq_client()
        service = crawler_cls(db, rabbitmq_client)
        await service.crawl(source_id)

switcher = {
    SourceType.NEWS_SITE: partial(_run_job, crawler_cls=HtmlCrawlService),
    SourceType.RSS: partial(_run_job, crawler_cls=RssCrawlService),
    SourceType.TELEGRAM_CHANNEL: partial(_run_job, crawler_cls=TelegramCrawlerService),
    SourceType.UNKNOWN: partial(_run_job, crawler_cls=FakeCrawlerService)
}

async def _run_scheduled_job(source_id: UUID) -> None:
    try:
        async with AsyncSessionLocal() as db:
            logger.info(f"Running scheduled job for source {source_id}")
            source = await db.scalar(select(Source).where(Source.id == source_id).where(Source.is_enabled.is_(True)))
            if not source:
                logger.warning(f"Source with id {source_id} not found")
                return
            handler = switcher.get(source.source_type)
            if not handler:
                logger.warning(f"No handler for source type {source.source_type}")
                return

            await handler(source_id=source_id)
            logger.info(f"Completed scheduled job for source {source_id}/{source.name}")
    except Exception:
        logger.exception(f"Error running scheduled job for source {source_id}")
        raise

def _get_worker_loop():
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop

@celery_app.task(name="schedule.tasks.run_scheduled_job")
def run_scheduled_job(source_id: str) -> None:
    loop = _get_worker_loop()
    return loop.run_until_complete(_run_scheduled_job(UUID(source_id)))
