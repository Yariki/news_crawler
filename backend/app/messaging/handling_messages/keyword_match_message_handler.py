import logging
from typing import Any

from app.services.notifications import notification_hub

logger = logging.getLogger(__name__)


async def keyword_match_message_handler(message: dict[str, Any]) -> None:
    """Broadcast a keyword match to connected WebSocket clients."""
    message_type = str(message["type"])
    await notification_hub.broadcast(message_type, message)
    logger.info(
        "Handled keyword match message type/message: %s/%s",
        message_type,
        message,
    )
