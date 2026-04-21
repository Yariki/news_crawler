from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.source.services.source_service import SourceService
from app.db.session import get_db
from app.schemas.source import SourceCreateUpdate
from app.services.crawler import CrawlService

router = APIRouter(prefix="/sources")


@router.get("")
async def get_source_list(db: AsyncSession = Depends(get_db)):
    return await SourceService(db).list_sources()


@router.get("/{source_id}")
async def get_source(source_id: UUID4, db: AsyncSession = Depends(get_db)):
    return await SourceService(db).get_source(source_id)


@router.post("", status_code=201)
async def create_source(data: SourceCreateUpdate, db: AsyncSession = Depends(get_db)):
    result = await SourceService(db).create_source(data)
    return result


@router.put("/{source_id}/run")
async def run_source(source_id: UUID4, db: AsyncSession = Depends(get_db)):
    return await CrawlService(db).run_source(source_id)
