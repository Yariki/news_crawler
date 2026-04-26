from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.source.services.source_service import SourceService
from app.db.base import PrimaryIdMixin
from app.db.session import get_db
from app.schemas.source import SourceCreateUpdate
from app.services.crawler import CrawlService

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
async def get_source_list(db: AsyncSession = Depends(get_db)):
    result = await SourceService(db).list_sources()
    return [
        {
            "id": _.id,
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


@router.get("/{source_id}")
async def get_source(source_id: UUID4, db: AsyncSession = Depends(get_db)):
    result = await SourceService(db).get_source(source_id)
    return {
        "id": result.id,
        "name": result.name,
        "base_url": result.base_url,
        "language": result.language,
        "source_type": result.source_type,
        "crawler_key": result.crawler_key,
        "is_enabled": result.is_enabled,
        "scrape_interval_minutes": result.scrape_interval_minutes,
    }


@router.post("", status_code=201)
async def create_source(data: SourceCreateUpdate, db: AsyncSession = Depends(get_db)):
    result = await SourceService(db).create_source(data)
    return {
        "id": result.id,
        "name": result.name,
        "base_url": result.base_url,
        "language": result.language,
        "source_type": result.source_type,
        "crawler_key": result.crawler_key,
        "is_enabled": result.is_enabled,
        "scrape_interval_minutes": result.scrape_interval_minutes,
    }


@router.put("/{source_id}/run")
async def run_source(source_id: UUID4, db: AsyncSession = Depends(get_db)):
    return await CrawlService(db).run_source(source_id)
