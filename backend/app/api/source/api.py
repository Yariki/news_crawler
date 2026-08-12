from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status as HTTPStatus
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.source.services.source_service import SourceService
from app.core.rbac import PermissionMode, RequiredPermissionsAndOwnership, OwnedResourceType
from app.db.session import get_db
from app.schemas.source import SourceCreateUpdate, SourceRead, SourceRunResponse
from app.core.config import settings
from app.utils.time import utc_now

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", status_code=200, response_model=list[SourceRead])
async def get_source_list(db: AsyncSession = Depends(get_db), \
                        access_control=Depends(RequiredPermissionsAndOwnership("source:read:own", mode=PermissionMode.ANY))):
    result = await SourceService(db, access_control).list_sources()  
    return result

@router.get("/{resource_id}", status_code=200, response_model=SourceRead)
async def get_source(resource_id: UUID4, db: AsyncSession = Depends(get_db), \
                        access_control=Depends(RequiredPermissionsAndOwnership("source:read:own", mode=PermissionMode.ANY, resource_type=OwnedResourceType.SOURCE))):
    result = await SourceService(db, access_control).get_source(resource_id)
    return result

@router.post("", status_code=201, response_model=SourceRead)
async def create_source(data: SourceCreateUpdate, db: AsyncSession = Depends(get_db), 
                        access_control=Depends(RequiredPermissionsAndOwnership("source:create:own", mode=PermissionMode.ANY))):
    """Creates a new source record in the database based on the provided SourceCreateUpdate object. It returns the created Source object."""
    result = await SourceService(db, access_control).create_source(data)
    return result

@router.post("/{resource_id}/run", status_code=200, response_model=SourceRunResponse)
async def run_source(resource_id: UUID4, db: AsyncSession = Depends(get_db), \
                        access_control=Depends(RequiredPermissionsAndOwnership("source:run:own", mode=PermissionMode.ALL, resource_type=OwnedResourceType.SOURCE))):
    """Dispatches a source for crawling based on the provided source ID. It checks if the source exists, is enabled, and is not currently being crawled. If all conditions are met, it updates the next_run_at field and dispatches the source for crawling using a Celery task. Returns a SourceRunResponse indicating the result of the operation."""
    source = await SourceService(db, access_control).get_source(resource_id)
    if not source or not source.is_enabled:
        raise HTTPException(status_code=HTTPStatus.HTTP_400_BAD_REQUEST, detail={
            "id": str(resource_id),
            "status": "error",
            "message": f"Source with id {resource_id} is not found or is disabled."
        })
    
    is_crawling_running = await SourceService(db,access_control).is_crawling_running(resource_id)
    if is_crawling_running:
        raise HTTPException(status_code=HTTPStatus.HTTP_400_BAD_REQUEST, detail={
            "id": str(resource_id),
            "status": "error",
            "message": f"Source with id {resource_id} is currently being crawled."
        })
    
    source.next_run_at = utc_now() + timedelta(minutes=source.scrape_interval_minutes)

    from app.schedule.celery_app import celery_app
    celery_app.send_task("schedule.tasks.run_scheduled_job", args=[str(resource_id)], queue=settings.celery_task_queue)

    await db.commit()

    return SourceRunResponse(
        id=resource_id,
        status="ok",
        message=f"Source with id {resource_id} has been dispatched for crawling."
    )
