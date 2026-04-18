from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.exceptions import HTTPException

from app.models.source import Source
from app.schemas.source import SourceCreate



class SourceService:
    def __init__(self, db: AsyncSession ) -> None:
        self.db = db

    async  def list_sources(self) -> list[Source]:
        query = (
            select(Source)
            .order_by(Source.name)
        )
        result = await self.db.scalars(query)
        return list(result.all())

    async def create_source(self, payload: SourceCreate) -> Source:
        source = Source(
            name=payload.name,
            base_url=str(payload.base_url),
            language=payload.language,
            source_type=payload.source_type,
            crawler_key=payload.crawler_key,
            scrape_interval_minutes=payload.scrape_interval_minutes,
            is_enabled=payload.is_enabled
        )
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        return source


    async def get_source(self, id: UUID4) -> Source:
        query = (
            select(Source)
            .where(Source.id == id)
        )
        result = await self.db.scalar(query)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="The Source is not found"
            )

        return result
    

