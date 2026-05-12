from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps.auth import require_non_forced_password_change, require_permission
from app.core.rbac import Permission, Role
from app.models.user import User
from app.api.source.services.source_service import SourceService
from app.db.session import get_db
from app.schemas.source import SourceCreateUpdate, SourceRead, SourceRunResponse
from app.services.scheduler import run_scheduled_job

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", status_code=200, response_model=list[SourceRead])
async def get_source_list(
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.SOURCE_READ)),
):
    result = await SourceService(db).list_sources(actor=actor)
    return [
        {
            "id": str(_.id),
            "name": _.name,
            "base_url": _.base_url,
            "language": _.language,
            "source_type": _.source_type,
            "crawler_key": _.crawler_key,
            "is_enabled": _.is_enabled,
            "scrape_interval_minutes": _.scrape_interval_minutes,
        }
        for _ in result
    ]

@router.get("/{source_id}", status_code=200, response_model=SourceRead)
async def get_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.SOURCE_READ)),
):
    result = await SourceService(db).get_source(source_id, actor=actor)
    return {
        "id": str(result.id),
        "name": result.name,
        "base_url": result.base_url,
        "language": result.language,
        "source_type": result.source_type,
        "crawler_key": result.crawler_key,
        "is_enabled": result.is_enabled,
        "scrape_interval_minutes": result.scrape_interval_minutes,
    }

@router.post("", status_code=201, response_model=SourceRead)
async def create_source(
    data: SourceCreateUpdate,
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.SOURCE_CREATE)),
    _: User | None = Depends(require_non_forced_password_change()),
):
    result = await SourceService(db).create_source(data, actor=actor)
    return {
        "id": str(result.id),
        "name": result.name,
        "base_url": result.base_url,
        "language": result.language,
        "source_type": result.source_type,
        "crawler_key": result.crawler_key,
        "is_enabled": result.is_enabled,
        "scrape_interval_minutes": result.scrape_interval_minutes,
    }

@router.post("/{source_id}/run", status_code=200, response_model=SourceRunResponse)
async def run_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.JOB_RUN)),
    _: User | None = Depends(require_non_forced_password_change()),
):
    if actor and Role(actor.role) == Role.TEAM_MEMBER:
        source = await SourceService(db).get_source(source_id, actor=actor)
        if str(source.owner_id) != str(actor.id):
            raise HTTPException(status_code=403, detail="Forbidden")
    result = await run_scheduled_job(source_id)
    return {"id": source_id, "status": "running" if result else "failed"}


@router.put("/{source_id}", status_code=200, response_model=SourceRead)
async def update_source(
    source_id: str,
    data: SourceCreateUpdate,
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.SOURCE_UPDATE)),
    _: User | None = Depends(require_non_forced_password_change()),
):
    result = await SourceService(db).update_source(source_id, data, actor=actor)
    return {
        "id": str(result.id),
        "name": result.name,
        "base_url": result.base_url,
        "language": result.language,
        "source_type": result.source_type,
        "crawler_key": result.crawler_key,
        "is_enabled": result.is_enabled,
        "scrape_interval_minutes": result.scrape_interval_minutes,
    }


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.SOURCE_DELETE)),
    _: User | None = Depends(require_non_forced_password_change()),
):
    await SourceService(db).delete_source(source_id, actor=actor)
