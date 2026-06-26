import logging

from app.messaging.messages.base import to_dict
from app.messaging.messages.keywords_match import KeywordsMatchMessage
from app.services.notifications import notification_hub

logger = logging.getLogger(__name__)

async def keyword_match_message_handler(message: KeywordsMatchMessage) -> None:
    """Broadcast a keyword match to connected WebSocket clients."""
    message_type = str(message.type) if message.type else "unknown"
    await notification_hub.broadcast(message_type, to_dict(message))    
    logger.info(
        "Handled keyword match message type/message: %s/%s",
        message_type,
        message,
    )
