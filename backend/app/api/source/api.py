from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.source.services.source_service import SourceService
from app.db.base import PrimaryIdMixin
from app.db.session import get_db
from app.schemas.job import CrawlJobRead
from app.schemas.source import SourceCreateUpdate, SourceRead, SourceRunResponse
from app.services.crawlers.html_crawler import HtmlCrawlService
from app.services.scheduler import run_scheduled_job

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
    result = await run_scheduled_job(source_id)
    return {"id": source_id, "status": "running" if result else "failed"}