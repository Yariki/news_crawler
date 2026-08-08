from fastapi import APIRouter, Depends
from app.core.rbac import RequiredPermissionsAndOwnership, PermissionMode, OwnedResourceType
from sqlalchemy import desc, select 
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.schemas.article import ArticleRead, SearchHit
from app.services.es import ElasticService
from app.db.scope_filter import filter_owned_resources

from app.db.session import get_db

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/recent", response_model=list[ArticleRead])
async def get_recent_articles(limit: int = 20, db: AsyncSession = Depends(get_db), access_control=Depends(RequiredPermissionsAndOwnership("article:read:own", mode=PermissionMode.ANY))):
    """Endpoint to retrieve recent articles."""
    
    query = (
        select(Article).order_by(desc(Article.published_at), desc(Article.id)).limit(limit)
    )
    query = filter_owned_resources(query=query, user_id=access_control.auth.user_id, model=Article, access_control=access_control)
    
    items = await db.scalars(query)
    
    return list(items.all())

@router.get("/search", response_model=list[SearchHit])
async def search_articles(q: str, access_control=Depends(RequiredPermissionsAndOwnership("article:read:own", mode=PermissionMode.ANY))):
    """Endpoint to search for articles based on a query string."""
    elastic_service = ElasticService()
    response = await elastic_service.search(q)
    hits: list[SearchHit] = []
    for hit in response["hits"]["hits"]:
        src = hit["_source"]
        
        if not access_control.is_any and access_control.auth.user_id != src.get("owner_id"):
            continue
        
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