import logging

from app.messaging.messages.base import to_dict
from ..messages.job_update import JobUpdateMessage
from ...services.notifications import notification_hub

logger = logging.getLogger(__name__)

async def job_update_message_handler(message: JobUpdateMessage) -> None:
    """Template method for handling job update messages."""
    payload = to_dict(message)
    await notification_hub.broadcast(message.type, payload)
    logger.info(f"Handled job update message type/message: {message.type}/{payload}")    
