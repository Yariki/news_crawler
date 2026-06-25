import logging
from typing import Any

from ...services.notifications import notification_hub

logger = logging.getLogger(__name__)


async def job_update_message_handler(message: dict[str, Any]) -> None:
    """Broadcast a crawl job update to connected WebSocket clients."""
    message_type = str(message["type"])
    await notification_hub.broadcast(message_type, message)
    logger.info("Handled job update message type/message: %s/%s", message_type, message)
