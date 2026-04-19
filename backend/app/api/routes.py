from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.article import Article
from app.schemas.article import ArticleRead, SearchHit
from app.schemas.dashboard import DashboardStats
from app.schemas.job import CrawlJobRead
from app.schemas.keyword import MonitoredKeywordCreate, MonitoredKeywordRead
from app.schemas.source import SourceCreate, SourceRead
from app.services.crawler import CrawlService
from app.services.es import elastic_service
from app.services.notifications import notification_hub

from app.api.keywords.api import router as keywords_router
from app.api.source.api import router as source_router

router = APIRouter(prefix="/api")

router.include_router(keywords_router)
router.include_router(source_router)

@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@router.get("/crawler-types")
async def get_crawler_types():
    return CrawlService.CRAWLER_TYPES

@router.get("/jobs", response_model=list[CrawlJobRead])
async def get_jobs(db: AsyncSession = Depends(get_db)):
    return await CrawlService(db).list_jobs()

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    return await CrawlService(db).dashboard_stats()

@router.get("/articles/recent", response_model=list[ArticleRead])
async def get_recent_articles(limit: int = 20, db: AsyncSession = Depends(get_db)):
    items = await db.scalars(select(Article).order_by(desc(Article.published_at), desc(Article.id)).limit(limit))
    return list(items.all())

@router.get("/search", response_model=list[SearchHit])
async def search_articles(q: str, db: AsyncSession = Depends(get_db)):
    _ = db
    response = await elastic_service.search(q)
    hits: list[SearchHit] = []
    for hit in response["hits"]["hits"]:
        src = hit["_source"]
        hits.append(
            SearchHit(
                article_id=src["article_id"],
                title=src["title"],
                url=src["url"],
                published_at=src.get("published_at"),
                source_name=src["source_name"],
                excerpt=(src.get("content_text") or "")[:300] + ("..." if len(src.get("content_text") or "") > 300 else ""),
                score=hit.get("_score"),
                is_alert=src.get("is_alert", False),
            )
        )
    return hits


@router.websocket("/ws/alerts")
async def alerts_ws(websocket: WebSocket):
    await notification_hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_hub.disconnect(websocket)



