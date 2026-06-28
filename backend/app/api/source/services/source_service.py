from app.models.status import Status
from app.models import CrawlJob
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.exceptions import HTTPException

from app.models.source import Source
from app.repositories.source_repository import SourceRepository
from app.schemas.source import SourceCreateUpdate
from app.utils.time import utc_now


class SourceService:

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self.rp = SourceRepository(db)

    async def list_sources(self) -> list[Source]:
        """Retrieves a list of all sources from the database and returns them as a list of Source objects."""
        return await self.rp.get_all_sources()

    async def create_source(self, payload: SourceCreateUpdate) -> Source:
        """Creates a new source record in the database based on the provided SourceCreateUpdate object. It returns the created Source object."""

        source_exist = await self.rp.get_source_by_url(str(payload.base_url))
        if source_exist:
            raise HTTPException(status_code=400, detail="The Source already exists")

        base_url = str(payload.base_url).rstrip("/")
        now = utc_now()
        source = Source(
            name=payload.name,
            base_url=base_url,
            language=payload.language,
            source_type=payload.source_type,
            crawler_key=payload.crawler_key,
            scrape_interval_minutes=payload.scrape_interval_minutes,
            is_enabled=payload.is_enabled,
            next_run_at=now
        )
        return await self.rp.add_source(source)

    async def get_source(self, id: str) -> Source:
        """Retrieves a source record from the database based on the provided source ID. If a record is found, it returns the Source object; otherwise, it raises an HTTPException with a 404 status code."""
        source = await self.rp.get_source_by_id(id)
        if not source:
            raise HTTPException(status_code=404, detail="The Source is not found")
        return source

    async def  get_due_sources(self, limit: int) -> list[Source]:
        """Retrieves a list of sources that are due for crawling based on their next_run_at field. It returns a list of Source objects that are ready to be crawled."""
        now = utc_now()
        return await self.rp.get_due_sources(now, limit)

    async def is_crawling_running(self, source_id: str) -> bool:
        """Checks if a source is currently being crawled."""
        job_exist_query = select(CrawlJob).where(CrawlJob.source_id == source_id).where(
            (CrawlJob.status == Status.RUNNING) | (CrawlJob.status == Status.WAITING)
        )
        result = await self._db.execute(job_exist_query)
        return result.scalar_one_or_none() is not None
