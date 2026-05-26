from fastapi import APIRouter, Depends
from sqlalchemy import desc, select 
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.schemas.article import ArticleRead, SearchHit
from app.services.es import elastic_service

from app.db.session import get_db

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/recent", response_model=list[ArticleRead])
async def get_recent_articles(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Endpoint to retrieve recent articles."""
    items = await db.scalars(select(Article).order_by(desc(Article.published_at), desc(Article.id)).limit(limit))
    return list(items.all())

@router.get("/search", response_model=list[SearchHit])
async def search_articles(q: str):
    """Endpoint to search for articles based on a query string."""
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