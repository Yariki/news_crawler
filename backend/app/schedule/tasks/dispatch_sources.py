from datetime import timedelta

from ...api.source.services.source_service import SourceService
from ...db.session import AsyncSessionLocal
from ...services.scheduler import run_scheduled_job

async def dispatch_sources(limit: int) -> int:
    """Retrieves a list of sources that are due for crawling and dispatches them for processing. It returns a list of Source objects that were dispatched."""
    async with AsyncSessionLocal() as db:
        service = SourceService(db)
        due_sources = await service.get_due_sources(limit=limit)
        for source in due_sources:
            await run_scheduled_job.delay(source.id)
        
        for source in due_sources:
            source.next_run_at = source.next_run_at + timedelta(minutes=source.scrape_interval_minutes)
            db.add(source)
        await db.commit()
    return len(due_sources)

