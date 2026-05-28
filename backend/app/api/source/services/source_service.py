from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.exceptions import HTTPException

from app.models.source import Source
from app.repositories.source_repository import SourceRepository
from app.schemas.source import SourceCreateUpdate


class SourceService:

    def __init__(self, db: AsyncSession) -> None:
        self.rp = SourceRepository(db)

    async def list_sources(self) -> list[Source]:
        """Retrieves a list of all sources from the database and returns them as a list of Source objects."""
        return await self.rp.get_all_sources()

    async def create_source(self, payload: SourceCreateUpdate) -> Source:
        """Creates a new source record in the database based on the provided SourceCreateUpdate object. It returns the created Source object."""
        base_url = str(payload.base_url).rstrip("/")
        source = Source(
            name=payload.name,
            base_url=base_url,
            language=payload.language,
            source_type=payload.source_type,
            crawler_key=payload.crawler_key,
            scrape_interval_minutes=payload.scrape_interval_minutes,
            is_enabled=payload.is_enabled,
        )
        return await self.rp.add_source(source)

    async def get_source(self, id: str) -> Source:
        """Retrieves a source record from the database based on the provided source ID. If a record is found, it returns the Source object; otherwise, it raises an HTTPException with a 404 status code."""
        source = await self.rp.get_source_by_id(id)
        if not source:
            raise HTTPException(status_code=404, detail="The Source is not found")
        return source
