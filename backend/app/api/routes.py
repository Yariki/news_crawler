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

router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/sources", response_model=list[SourceRead])
async def get_sources(db: AsyncSession = Depends(get_db)):
    return await CrawlService(db).list_sources()


@router.post("/sources", response_model=SourceRead)
async def create_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)):
    return await CrawlService(db).create_source(payload)


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


@router.post("/sources/{source_id}/run", response_model=CrawlJobRead)
async def run_source_now(source_id: int, db: AsyncSession = Depends(get_db)):
    return await CrawlService(db).run_source(source_id)


@router.get("/keywords", response_model=list[MonitoredKeywordRead])
async def get_keywords(db: AsyncSession = Depends(get_db)):
    return await CrawlService(db).list_keywords()


@router.post("/keywords", response_model=MonitoredKeywordRead)
async def create_keyword(payload: MonitoredKeywordCreate, db: AsyncSession = Depends(get_db)):
    return await CrawlService(db).create_keyword(payload.keyword)


@router.delete("/keywords/{keyword_id}", status_code=204)
async def delete_keyword(keyword_id: int, db: AsyncSession = Depends(get_db)):
    await CrawlService(db).delete_keyword(keyword_id)


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
