from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.exceptions import HTTPException

from app.core.rbac import Role
from app.models.monitored_keyword import MonitoredKeyword
from app.models.user import User
from app.schemas.keyword import MonitoredKeywordUpdate
from app.services.keyword_detector import normalize_keyword


class KeywordService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_keywords(self, actor: User | None = None) -> list[MonitoredKeyword]:
        query = select(MonitoredKeyword).order_by(MonitoredKeyword.keyword)
        if actor is not None:
            role = Role(actor.role)
            if role == Role.TEAM_MEMBER:
                query = query.where(MonitoredKeyword.owner_id == actor.id)
            elif role in {Role.TEAM_LEAD, Role.TEAM_VIEWER}:
                team_user_ids = select(User.id).where(User.team_id == actor.team_id)
                query = query.where(MonitoredKeyword.owner_id.in_(team_user_ids))
        result = await self.db.scalars(query)
        return list(result.all())

    async def get_active_keywords(self, actor: User | None = None) -> list[str]:
        query = (
            select(MonitoredKeyword.keyword)
            .where(MonitoredKeyword.is_enabled.is_(True))
            .order_by(MonitoredKeyword.keyword)
        )
        if actor is not None:
            role = Role(actor.role)
            if role == Role.TEAM_MEMBER:
                query = query.where(MonitoredKeyword.owner_id == actor.id)
            elif role in {Role.TEAM_LEAD, Role.TEAM_VIEWER}:
                team_user_ids = select(User.id).where(User.team_id == actor.team_id)
                query = query.where(MonitoredKeyword.owner_id.in_(team_user_ids))
        result = await self.db.scalars(query)
        keywords = [normalize_keyword(value) for value in result.all() if value]
        return keywords

    async def get_keyword(self, keyword_id: UUID4, actor: User | None = None) -> MonitoredKeyword:
        item = await self.db.get(MonitoredKeyword, keyword_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Keyword not found")
        if actor is not None:
            role = Role(actor.role)
            if role == Role.TEAM_MEMBER and str(item.owner_id) != str(actor.id):
                raise HTTPException(status_code=404, detail="Keyword not found")
            if role in {Role.TEAM_LEAD, Role.TEAM_VIEWER}:
                if item.owner_id is None:
                    raise HTTPException(status_code=404, detail="Keyword not found")
                owner_team = await self.db.scalar(select(User.team_id).where(User.id == item.owner_id))
                if owner_team != actor.team_id:
                    raise HTTPException(status_code=404, detail="Keyword not found")
        return item

    async def create_keyword(self, keyword: str, actor: User | None = None) -> MonitoredKeyword:
        normalized = normalize_keyword(keyword)
        query = select(MonitoredKeyword).where(MonitoredKeyword.keyword == normalized)
        if actor is not None and Role(actor.role) == Role.TEAM_MEMBER:
            query = query.where(MonitoredKeyword.owner_id == actor.id)
        existing = await self.db.scalar(query)
        if existing:
            return existing
        item = MonitoredKeyword(keyword=normalized, is_enabled=True, owner_id=actor.id if actor else None)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item
    
    async def update_keyword(self, keyword_id: UUID4, keyword_update: MonitoredKeywordUpdate, actor: User | None = None) -> MonitoredKeyword:
        keyword = await self.get_keyword(keyword_id, actor=actor)

        if not keyword:
            raise HTTPException(status_code=404, detail="Keyword not found")
        
        keyword.keyword = normalize_keyword(keyword_update.keyword)
        keyword.is_enabled = keyword_update.is_enabled
        self.db.add(keyword)
        await self.db.commit()
        await self.db.refresh(keyword)
        return keyword

    async def delete_keyword(self, keyword_id: UUID4, actor: User | None = None) -> None:
        item = await self.get_keyword(keyword_id, actor=actor)
        await self.db.delete(item)
        await self.db.commit()
