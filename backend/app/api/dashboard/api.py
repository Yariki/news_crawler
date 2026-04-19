from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dashboard.services.dashbord_service import DashboardService
from app.api.source.services.source_service import SourceService
from app.db.session import get_db
from app.schemas.source import SourceCreate
from app.services.crawler import CrawlService


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)

@router.get("/jobs")
async def get_jobs(db: AsyncSession = Depends(get_db)):
    return DashboardService(db).list_jobs()


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    return DashboardService(db).dashboard_stats();



