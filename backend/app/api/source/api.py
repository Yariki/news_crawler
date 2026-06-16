from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.source.services.source_service import SourceService
from app.db.session import get_db
from app.schemas.source import SourceCreateUpdate, SourceRead, SourceRunResponse
from app.schedule.tasks.check_source import run_scheduled_job
from ...core.config import settings

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
    result = await SourceService(db).create_source(data)
    return result

@router.post("/{source_id}/run", status_code=200, response_model=SourceRunResponse)
async def run_source(source_id: str, db: AsyncSession = Depends(get_db)):
    
    source = await SourceService(db).get_source(source_id)
    if not source or not source.is_enabled:
        return SourceRunResponse(
            id=source_id,
            status="error",
            message=f"Source with id {source_id} is not found or is disabled."
        )
    
    from app.schedule.celery_app import celery_app
    celery_app.send_task("schedule.tasks.run_scheduled_job", args=[str(source_id)], queue=settings.celery_task_queue)

    run_scheduled_job.delay(source_id)
    return SourceRunResponse(
        id=source_id,
        status="ok",
        message=f"Source with id {source_id} has been dispatched for crawling."
    )
    
    