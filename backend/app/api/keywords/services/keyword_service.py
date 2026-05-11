from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from fastapi.exceptions import HTTPException

from app.models.monitored_keyword import MonitoredKeyword
from app.schemas.keyword import MonitoredKeywordUpdate
from app.services.keyword_detector import normalize_keyword


class KeywordService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_keywords(self, owner_id: UUID) -> list[MonitoredKeyword]:
        query = select(MonitoredKeyword).where(MonitoredKeyword.owner_id == owner_id).order_by(MonitoredKeyword.keyword)
        result = await self.db.scalars(query)
        return list(result.all())

    async def get_active_keywords(self, owner_id: UUID) -> list[str]:
        result = await self.db.scalars(
            select(MonitoredKeyword.keyword)
            .where(MonitoredKeyword.is_enabled.is_(True), MonitoredKeyword.owner_id == owner_id)
            .order_by(MonitoredKeyword.keyword)
        )
        keywords = [normalize_keyword(value) for value in result.all() if value]
        return keywords

    async def get_keyword(self, keyword_id: UUID4, owner_id: UUID) -> MonitoredKeyword:
        item = await self.db.scalar(
            select(MonitoredKeyword).where(MonitoredKeyword.id == keyword_id, MonitoredKeyword.owner_id == owner_id)
        )
        if item is None:
            raise HTTPException(status_code=404, detail="Keyword not found")
        return item

    async def create_keyword(self, keyword: str, owner_id: UUID) -> MonitoredKeyword:
        normalized = normalize_keyword(keyword)
        existing = await self.db.scalar(
            select(MonitoredKeyword).where(MonitoredKeyword.keyword == normalized, MonitoredKeyword.owner_id == owner_id)
        )
        if existing:
            return existing
        item = MonitoredKeyword(keyword=normalized, is_enabled=True, owner_id=owner_id)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item
    
    async def update_keyword(self, keyword_id: UUID4, owner_id: UUID, keyword_update: MonitoredKeywordUpdate) -> MonitoredKeyword:
        keyword = await self.get_keyword(keyword_id, owner_id)

        if not keyword:
            raise HTTPException(status_code=404, detail="Keyword not found")
        
        keyword.keyword = normalize_keyword(keyword_update.keyword)
        keyword.is_enabled = keyword_update.is_enabled
        self.db.add(keyword)
        await self.db.commit()
        await self.db.refresh(keyword)
        return keyword

    async def delete_keyword(self, keyword_id: UUID4, owner_id: UUID) -> None:
        item = await self.db.scalar(
            select(MonitoredKeyword).where(MonitoredKeyword.id == keyword_id, MonitoredKeyword.owner_id == owner_id)
        )
        if item is None:
            return
        await self.db.delete(item)
        await self.db.commit()
