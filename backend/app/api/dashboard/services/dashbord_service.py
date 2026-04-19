from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CrawlJob, Source, Article, MonitoredKeyword
from app.services.es import elastic_service


class DashboardService:

    def __init__(self, db: AsyncSession):
        self.db = db


    async def list_jobs(self, limit: int = 50) -> list[CrawlJob]:
        result = await self.db.scalars(select(CrawlJob).order_by(desc(CrawlJob.started_at)).limit(limit))
        return list(result.all())

    async def dashboard_stats(self) -> dict:
        from sqlalchemy import func
        return {
            "sources_total": await self.db.scalar(select(func.count(Source.id))) or 0,
            "sources_enabled": await self.db.scalar(
                select(func.count(Source.id)).where(Source.is_enabled.is_(True))) or 0,
            "articles_total": await self.db.scalar(select(func.count(Article.id))) or 0,
            "alerts_total": await self.db.scalar(select(func.count(Article.id)).where(Article.is_alert.is_(True))) or 0,
            "jobs_total": await self.db.scalar(select(func.count(CrawlJob.id))) or 0,
            "keywords_total": await self.db.scalar(
                select(func.count(MonitoredKeyword.id)).where(MonitoredKeyword.is_enabled.is_(True))) or 0,
            "elasticsearch_document_count": await elastic_service.count(),
        }
