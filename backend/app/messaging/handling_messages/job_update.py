import logging

from app.db.session import AsyncSessionLocal
from app.models.status import Status
from app.repositories.crawljob_repository import CrawlJobRepository

from ...messaging.messages.job_finished import JobFinishedMessage
from ...messaging.messages.base import convert_dict_to_message
from ...services.notifications import notification_hub

logger = logging.getLogger(__name__)


async def handle_job_update(message: dict) -> None:
    msg = JobFinishedMessage(**convert_dict_to_message(message, JobFinishedMessage).__dict__)
    if not msg.job_id and not msg.source_id:
        logger.info(f"Received job update for job {msg.job_id} and source {msg.source_id}")
        return
    
    async with AsyncSessionLocal() as db:
        job = await CrawlJobRepository(db).get_crawl_job_by_id(str(msg.job_id))
        if not job:
            logger.warning(f"Crawl job with id {msg.job_id} not found")
            return
        if job.status != Status.COMPLETED:
            logger.info(f"Job {msg.job_id} is not finished yet, current status: {job.status}")
            return
        await notification_hub.broadcast(
            "job_finished", {
                "job_id": str(msg.job_id),
                "status": job.status,
            }
        )
        logger.info(f"Job {msg.job_id} has finished with status: {job.status}")