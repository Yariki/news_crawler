from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status as HTTPStatus
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.source.services.source_service import SourceService
from app.db.session import get_db
from app.schemas.source import SourceCreateUpdate, SourceRead, SourceRunResponse
from app.core.config import settings
from app.utils.time import utc_now

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", status_code=200, response_model=list[SourceRead])
async def get_source_list(db: AsyncSession = Depends(get_db)):
    result = await SourceService(db).list_sources()
    return result

@router.get("/{source_id}", status_code=200, response_model=SourceRead)
async def get_source(source_id: str, db: AsyncSession = Depends(get_db)):
    result = await SourceService(db).get_source(source_id)
    return result

@router.post("", status_code=201, response_model=SourceRead)
async def create_source(data: SourceCreateUpdate, db: AsyncSession = Depends(get_db)):
    """Creates a new source record in the database based on the provided SourceCreateUpdate object. It returns the created Source object."""
    result = await SourceService(db).create_source(data)
    return result

@router.post("/{source_id}/run", status_code=200, response_model=SourceRunResponse)
async def run_source(source_id: str, db: AsyncSession = Depends(get_db)):
    """Dispatches a source for crawling based on the provided source ID. It checks if the source exists, is enabled, and is not currently being crawled. If all conditions are met, it updates the next_run_at field and dispatches the source for crawling using a Celery task. Returns a SourceRunResponse indicating the result of the operation."""
    async with db.begin():
        source = await SourceService(db).get_source(source_id)
        if not source or not source.is_enabled:
            raise HTTPException(status_code=HTTPStatus.HTTP_400_BAD_REQUEST, detail={
                "id": source_id,
                "status": "error",
                "message": f"Source with id {source_id} is not found or is disabled."
            })
        
        is_crawling_running = await SourceService(db).is_crawling_running(source_id)
        if is_crawling_running:
            raise HTTPException(status_code=HTTPStatus.HTTP_400_BAD_REQUEST, detail={
                "id": source_id,
                "status": "error",
                "message": f"Source with id {source_id} is currently being crawled."
            })
        
        source.next_run_at = utc_now() + timedelta(minutes=source.scrape_interval_minutes)

        from app.schedule.celery_app import celery_app
        celery_app.send_task("schedule.tasks.run_scheduled_job", args=[str(source_id)], queue=settings.celery_task_queue)

    return SourceRunResponse(
        id=source_id,
        status="ok",
        message=f"Source with id {source_id} has been dispatched for crawling."
    )
