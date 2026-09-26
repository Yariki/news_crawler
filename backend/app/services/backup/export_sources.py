
from app.api.source.services.source_service import SourceService
from app.core.rbac import PermissionGranted
from pydantic import BaseModel
from fastapi import HTTPException, status as HTTPStatus
from app.db.scope_filter import filter_owned_resources
from app.db.session import AsyncSession
from sqlalchemy import select
from app.models import Source
from uuid import UUID
import json

from app.schemas.source import SourceCreateUpdate


class ImportError(BaseModel):
    index: int
    base_url: str | None
    error: str



async def export_sources(db: AsyncSession, owner_id: UUID, access_granted: PermissionGranted) -> bytes:
    query = (
        select(Source.base_url, Source.name, Source.language, Source.source_type, Source.crawler_key, Source.scrape_interval_minutes, Source.is_enabled)
    )
    query = filter_owned_resources(query=query, user_id=owner_id, model=Source, access_control=access_granted)
    result = (await db.execute(query)).mappings().all()

    return json.dumps([dict(row) for row in result]).encode('utf-8')


async def import_sources(db: AsyncSession, owner_id: UUID, access_granted: PermissionGranted, data: bytes) -> bool:
    try:
        sources = json.loads(data.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=HTTPStatus.HTTP_400_BAD_REQUEST, detail="Invalid JSON data")
    if not isinstance(sources, list):
        raise HTTPException(status_code=HTTPStatus.HTTP_400_BAD_REQUEST, detail="JSON data must be a list of sources")

    source_service = SourceService(
        db=db,
        access_control=access_granted
    )

    existing_sources = await source_service.list_sources()
    existing_urls = [source.base_url.rstrip('/') for source in existing_sources]

    import_errors = []  # List to store import errors
    for index, item in enumerate(sources):
        base_url = item.get('base_url').rstrip('/') if isinstance(item, dict) else None
        try:
            if base_url in existing_urls:
                continue

            payload = SourceCreateUpdate.model_validate(item)
            await source_service.create_source(payload=payload)
        except Exception as e:
            import_errors.append(ImportError(index=index, base_url=base_url, error=str(e)))

    if import_errors:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=[error.dict() for error in import_errors]
        )
    return True

