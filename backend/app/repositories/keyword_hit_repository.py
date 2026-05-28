


from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.keyword_hit import KeywordHit


class KeywordHitRepository:
    """Repository for managing keyword hit records in the database. Provides methods for creating, retrieving, and deleting keyword hit entries, as well as querying hits by keyword or article ID."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_keyword_hit(self, new_hit: KeywordHit) -> KeywordHit:
        """Creates a new keyword hit record in the database."""
        
        self.db.add(new_hit)
        await self.db.commit()
        await self.db.refresh(new_hit)
        return new_hit

    async def get_hits_by_keyword(self, keyword: str) -> list[KeywordHit]:
        """Retrieves all keyword hit records for a specific keyword."""
        result = await self.db.execute(
            select(KeywordHit).where(KeywordHit.keyword == keyword).order_by(KeywordHit.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_hits_by_article_id(self, article_id: str) -> list[KeywordHit]:
        """Retrieves all keyword hit records for a specific article ID."""
        result = await self.db.execute(
            select(KeywordHit).where(KeywordHit.article_id == article_id).order_by(KeywordHit.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_hits_by_article_id(self, article_id: str) -> int:
        """Deletes all keyword hit records associated with a specific article ID. Returns the number of records deleted."""
        result = await self.db.execute(
            delete(KeywordHit).where(KeywordHit.article_id == article_id)
        )
        await self.db.commit()
        return result.rowcount