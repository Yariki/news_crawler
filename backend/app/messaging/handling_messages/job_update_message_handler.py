import logging
from typing import Any

from app.messaging.messages.base import to_dict
from app.messaging.messages.job_update import JobUpdateMessage

from ...services.notifications import notification_hub

logger = logging.getLogger(__name__)


async def job_update_message_handler(message: JobUpdateMessage) -> None:
    """Broadcast a crawl job update to connected WebSocket clients."""
    message_type = str(message.type) if message.type else "unknown"
    await notification_hub.broadcast(message_type, to_dict(message))
    logger.info("Handled job update message type/message: %s/%s", message_type, message)
