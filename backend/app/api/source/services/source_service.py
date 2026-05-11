from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from fastapi.exceptions import HTTPException

from app.models.source import Source
from app.schemas.source import SourceCreateUpdate


class SourceService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_sources(self, owner_id: UUID) -> list[Source]:
        query = select(Source).where(Source.owner_id == owner_id).order_by(Source.name)
        result = await self.db.scalars(query)
        return list(result.all())

    async def create_source(self, payload: SourceCreateUpdate, owner_id: UUID) -> Source:
        base_url = str(payload.base_url).rstrip("/")
        source = Source(
            name=payload.name,
            owner_id=owner_id,
            base_url=base_url,
            language=payload.language,
            source_type=payload.source_type,
            crawler_key=payload.crawler_key,
            scrape_interval_minutes=payload.scrape_interval_minutes,
            is_enabled=payload.is_enabled,
        )
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def get_source(self, id: str, owner_id: UUID) -> Source:
        query = select(Source).where(Source.id == id, Source.owner_id == owner_id)
        result = await self.db.scalar(query)

        if not result:
            raise HTTPException(status_code=404, detail="The Source is not found")

        return result
