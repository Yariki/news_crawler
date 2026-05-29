from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dashboard.services.dashbord_service import DashboardService
from app.db.session import get_db
from app.schemas.dashboard import DashboardStats
from app.schemas.job import CrawlJobRead
from app.schemas.source import SourceRead

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get("/jobs", response_model=list[CrawlJobRead])
async def get_jobs(db: AsyncSession = Depends(get_db)):
    result = await DashboardService(db).list_jobs()
    return result


@router.get("/stats", status_code=200, response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    result = await DashboardService(db).dashboard_stats()
    return result
