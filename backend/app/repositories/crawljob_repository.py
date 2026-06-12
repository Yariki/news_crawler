


from app.models.crawl_job import CrawlJob
from app.models.status import Status


class CrawlJobRepository:
    """Repository class responsible for managing CrawlJob records in the database. It provides methods to create new crawl jobs and update existing crawl jobs. This class abstracts away the database interactions related to the CrawlJob model, allowing other parts of the application to work with CrawlJob objects without needing to know about the underlying database structure."""
    def __init__(self, db):
        self.db = db
        
        
    async def create_crawl_job(self, source_id: str, status: Status) -> CrawlJob:
        """Creates a new crawl job record in the database for a given source ID and status. It returns the created CrawlJob object."""
        job = CrawlJob(source_id=source_id, status=status)
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job
    
    async def update_crawl_job(self, params: CrawlJob) -> None:
        """Updates an existing crawl job record in the database with new data from the provided CrawlJob object."""
        job = await self.db.get(CrawlJob, params.id)
        if not job:
            raise ValueError("CrawlJob not found")

        for key, value in params.__dict__.items():
            setattr(job, key, value)

        await self.db.commit()
        await self.db.refresh(job)
        
    async def get_crawl_job_by_id(self, job_id: str) -> CrawlJob | None:
        """Retrieves a crawl job record from the database by its ID. It returns the CrawlJob object if found, or None if no matching record exists."""
        return await self.db.get(CrawlJob, job_id)