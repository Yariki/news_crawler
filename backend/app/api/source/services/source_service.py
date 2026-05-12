from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.exceptions import HTTPException

from app.core.rbac import Role
from app.models.source import Source
from app.models.user import User
from app.schemas.source import SourceCreateUpdate


class SourceService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_sources(self, actor: User | None = None) -> list[Source]:
        query = select(Source).order_by(Source.name)
        if actor is not None:
            role = Role(actor.role)
            if role == Role.TEAM_MEMBER:
                query = query.where(Source.owner_id == actor.id)
            elif role in {Role.TEAM_LEAD, Role.TEAM_VIEWER}:
                team_user_ids = select(User.id).where(User.team_id == actor.team_id)
                query = query.where(Source.owner_id.in_(team_user_ids))
        result = await self.db.scalars(query)
        return list(result.all())

    async def create_source(self, payload: SourceCreateUpdate, actor: User | None = None) -> Source:
        base_url = str(payload.base_url).rstrip("/")
        source = Source(
            name=payload.name,
            base_url=base_url,
            language=payload.language,
            source_type=payload.source_type,
            crawler_key=payload.crawler_key,
            scrape_interval_minutes=payload.scrape_interval_minutes,
            is_enabled=payload.is_enabled,
            owner_id=actor.id if actor else None,
        )
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def get_source(self, id: str, actor: User | None = None) -> Source:
        query = select(Source).where(Source.id == id)
        result = await self.db.scalar(query)

        if not result:
            raise HTTPException(status_code=404, detail="The Source is not found")
        if actor is not None:
            role = Role(actor.role)
            if role == Role.TEAM_MEMBER and str(result.owner_id) != str(actor.id):
                raise HTTPException(status_code=404, detail="The Source is not found")
            if role in {Role.TEAM_LEAD, Role.TEAM_VIEWER}:
                if result.owner_id is None:
                    raise HTTPException(status_code=404, detail="The Source is not found")
                owner_team = await self.db.scalar(select(User.team_id).where(User.id == result.owner_id))
                if owner_team != actor.team_id:
                    raise HTTPException(status_code=404, detail="The Source is not found")

        return result

    async def update_source(self, id: str, payload: SourceCreateUpdate, actor: User | None = None) -> Source:
        source = await self.get_source(id, actor=actor)
        source.name = payload.name
        source.base_url = str(payload.base_url).rstrip("/")
        source.language = payload.language
        source.source_type = payload.source_type
        source.crawler_key = payload.crawler_key
        source.scrape_interval_minutes = payload.scrape_interval_minutes
        source.is_enabled = payload.is_enabled
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def delete_source(self, id: str, actor: User | None = None) -> None:
        source = await self.get_source(id, actor=actor)
        await self.db.delete(source)
        await self.db.commit()
