from datetime import timedelta

from app.utils.time import utc_now

from ...api.source.services.source_service import SourceService
from ...db.session import AsyncSessionLocal
from ...schedule.tasks.check_source import run_scheduled_job
import logging

logger = logging.getLogger(__name__)

async def dispatch_due_sources(limit: int) -> int:
    """Retrieves a list of sources that are due for crawling and dispatches them for processing. It returns a list of Source objects that were dispatched."""
    async with AsyncSessionLocal() as db:
        service = SourceService(db)
        due_sources = await service.get_due_sources(limit=limit)
        for source in due_sources:
            run_scheduled_job.delay(str(source.id))
            logger.info(f"Dispatched source {source.id} for crawling.")
        now = utc_now()
        for source in due_sources:
            source.next_run_at = now + timedelta(minutes=source.scrape_interval_minutes)
            db.add(source)
        await db.commit()
    return len(due_sources)
