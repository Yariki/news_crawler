from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dashboard.services.dashbord_service import DashboardService
from app.db.session import get_db
from app.schemas.dashboard import DashboardStats
from app.schemas.source import SourceRead

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get("/jobs")
async def get_jobs(db: AsyncSession = Depends(get_db)):
    result = await DashboardService(db).list_jobs()
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
        }
        for _ in result
    ]


@router.get("/stats", status_code=200, response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    result = await DashboardService(db).dashboard_stats()
    return DashboardStats(
        sources_total=result["sources_total"],
        sources_enabled=result["sources_enabled"],
        articles_total=result["articles_total"],
        alerts_total=result["alerts_total"],
        jobs_total=result["jobs_total"],
        keywords_total=result["keywords_total"],
        elasticsearch_document_count=result["elasticsearch_document_count"],
    )
