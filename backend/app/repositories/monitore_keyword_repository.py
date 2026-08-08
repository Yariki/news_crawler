from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from fastapi.exceptions import HTTPException
from app.repositories.base_auth_repository import BaseAuthRepository, PermissionGranted
from app.models.monitored_keyword import MonitoredKeyword
from app.models.user import User
from app.schemas.keyword import MonitoredKeywordUpdate
from app.services.keyword_detector import normalize_keyword


class MonitoreKeywordRepository(BaseAuthRepository):
    def __init__(self, db: AsyncSession, access_control: PermissionGranted) -> None:
        self.db = db
        self.access_control = access_control

    async def list_keywords(self, user_id: UUID) -> list[MonitoredKeyword]:
        query = select(MonitoredKeyword).where(MonitoredKeyword.owner_id == user_id).order_by(MonitoredKeyword.keyword)
        query = self.filter_owned_resources(query, MonitoredKeyword)
        result = await self.db.scalars(query)
        return list(result.all())

    async def get_active_keywords(self) -> list[str]:
        result = await self.db.scalars(
            select(MonitoredKeyword.keyword)
            .where(MonitoredKeyword.is_enabled.is_(True))
            .order_by(MonitoredKeyword.keyword)
        )
        query = self.filter_owned_resources(result, MonitoredKeyword)
        keywords = [normalize_keyword(value) for value in result.all() if value]
        return keywords

    async def get_keyword(self, keyword_id: UUID4) -> MonitoredKeyword:
        item = await self.db.get(MonitoredKeyword, keyword_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Keyword not found")
        return item

    async def create_keyword(self, keyword: str, user_id: UUID) -> MonitoredKeyword:
        normalized = normalize_keyword(keyword)
        existing = await self.db.scalar(
            select(MonitoredKeyword).where(MonitoredKeyword.keyword == normalized)
        )
        if existing:
            return existing
        item = MonitoredKeyword(keyword=normalized, is_enabled=True, owner_id=user_id)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_keyword(self, keyword_id: UUID4, keyword_update: MonitoredKeywordUpdate) -> MonitoredKeyword:
        keyword = await self.get_keyword(keyword_id)

        if not keyword:
            raise HTTPException(status_code=404, detail="Keyword not found")

        keyword.keyword = normalize_keyword(keyword_update.keyword)
        keyword.is_enabled = keyword_update.is_enabled
        self.db.add(keyword)
        await self.db.commit()
        await self.db.refresh(keyword)
        return keyword

    async def delete_keyword(self, keyword_id: UUID4) -> None:
        item = await self.db.get(MonitoredKeyword, keyword_id)
        if item is None:
            return
        await self.db.delete(item)
        await self.db.commit()
