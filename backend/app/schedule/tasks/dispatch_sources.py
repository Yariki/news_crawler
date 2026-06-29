from datetime import timedelta

from app.utils.time import utc_now

from ...api.source.services.source_service import SourceService
from ...db.session import AsyncSessionLocal
from ...core.config import settings

import logging

logger = logging.getLogger(__name__)

async def dispatch_due_sources(limit: int) -> int:
    """Dispatches due sources for crawling and returns the number of sources dispatched."""
    
    due_source_count = 0
    async with AsyncSessionLocal() as db:
        async with db.begin():
            service = SourceService(db)
            due_sources = await service.get_due_sources(limit=limit)
            due_source_count = len(due_sources)
            now = utc_now()
            for source in due_sources:
                source.next_run_at = now + timedelta(minutes=source.scrape_interval_minutes)
            
            from ...schedule.celery_app import celery_app

            for source in due_sources:
                celery_app.send_task("schedule.tasks.run_scheduled_job", args=[str(source.id)], queue=settings.celery_task_queue)
                logger.info(f"Dispatched source {source.id} for crawling.")
        
    return due_source_count
