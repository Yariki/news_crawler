from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from uuid import UUID

from app.models import CrawlJob, Source, Article, MonitoredKeyword
from app.services.es import elastic_service


class DashboardService:

    def __init__(self, db: AsyncSession):
        self.db = db


    async def list_jobs(self, owner_id: UUID, limit: int = 50) -> list[CrawlJob]:
        result = await self.db.scalars(
            select(CrawlJob).where(CrawlJob.owner_id == owner_id).order_by(desc(CrawlJob.started_at)).limit(limit)
        )
        return list(result.all())

    async def dashboard_stats(self, owner_id: UUID) -> dict:
        return {
            "sources_total": await self.db.scalar(select(func.count(Source.id)).where(Source.owner_id == owner_id)) or 0,
            "sources_enabled": await self.db.scalar(
                select(func.count(Source.id)).where(Source.is_enabled.is_(True), Source.owner_id == owner_id)) or 0,
            "articles_total": await self.db.scalar(select(func.count(Article.id)).where(Article.owner_id == owner_id)) or 0,
            "alerts_total": await self.db.scalar(
                select(func.count(Article.id)).where(Article.is_alert.is_(True), Article.owner_id == owner_id)
            ) or 0,
            "jobs_total": await self.db.scalar(select(func.count(CrawlJob.id)).where(CrawlJob.owner_id == owner_id)) or 0,
            "keywords_total": await self.db.scalar(
                select(func.count(MonitoredKeyword.id)).where(
                    MonitoredKeyword.is_enabled.is_(True), MonitoredKeyword.owner_id == owner_id
                )
            ) or 0,
            "elasticsearch_document_count": await elastic_service.count(),
        }
