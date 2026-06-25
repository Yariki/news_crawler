from app.messaging.messages.base import to_dict
from app.messaging.messages.keywords_match import KeywordsMatchMessage
import logging
from app.services.notifications import notification_hub

logger = logging.getLogger(__name__)


async def keyword_match_message_handler(message: KeywordsMatchMessage) -> None:
    """Template method for handling keyword match messages."""
    payload = to_dict(message)
    await notification_hub.broadcast(message.type, payload)
    logger.info(f"Handled keyword match message type/message: {message.type}/{payload}")    
