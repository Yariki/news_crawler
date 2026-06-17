import logging

from ...db.session import AsyncSessionLocal
from ...models.status import Status
from ...services.notifications import notification_hub

logger = logging.getLogger(__name__)


async def handle_template_method(message: dict) -> None:
    """template method for handling job update messages. It updates the status of the corresponding CrawlJob in the database and sends a notification if the job is completed or failed."""
    logger.info(f"Handling job update message: {message}")