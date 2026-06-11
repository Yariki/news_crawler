from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source


class SourceRepository:
    """Repository class responsible for managing Source records in the database. It provides methods to retrieve all sources and get a source by its ID. This class abstracts away the database interactions related to the Source model, allowing other parts of the application to work with Source objects without needing to know about the underlying database structure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_sources(self):
        """Retrieves all source records from the database and returns them as a list of Source objects."""

        query = select(Source).order_by(Source.name)
        result = await self.db.scalars(query)
        return list(result.all())

    async def add_source(self, source: Source) -> Source:
        """Adds a new source record to the database based on the provided Source object."""
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def get_source_by_id(self, source_id):
        """Retrieves a source record from the database based on the provided source ID. If a record is found, it returns the Source object; otherwise, it returns None."""
        query = select(Source).where(Source.id == source_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_due_sources(self, now: datetime, limit: int) -> list[Source]:
        """Retrieves a list of sources that are due for crawling based on their next_run_at field. It returns a list of Source objects that are ready to be crawled."""
        query = (
            select(Source)
            .where(Source.is_enabled.is_(True))
            .where(Source.next_run_at <= now)
            .limit(limit)
            .order_by(Source.next_run_at)
        )
        result = await self.db.scalars(query)
        return list(result.all())
