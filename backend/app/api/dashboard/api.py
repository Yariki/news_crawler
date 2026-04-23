from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dashboard.services.dashbord_service import DashboardService
from app.db.session import get_db

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get("/jobs")
async def get_jobs(db: AsyncSession = Depends(get_db)):
    result = DashboardService(db).list_jobs()
    return [
        {
            "id": _.id,
            "source_id": _.source_id,
            "status": _.status,
            "started_at": _.started_at,
            "finished_at": _.finished_at,
            "articles_found": _.articles_found,
            "articles_created": _.articles_created,
            "error_message": _.error_message,
        } for _ in result
    ]


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    return DashboardService(db).dashboard_stats()
