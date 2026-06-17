import logging

from ...messaging.messages.base import MessageTypes
from .handle_template import handle_template

logger = logging.getLogger(__name__)


HANDLERS = {
    MessageTypes.JOB_UPDATE: handle_template,
}

async def handle_message(message: dict) -> None:
    """Handle incoming messages from RabbitMQ."""
    logger.debug(f"Received message: {message}")
    message_type = message.get("type")
    handler = HANDLERS.get(MessageTypes(message_type)) if message_type else None
    if not handler:
        logger.warning(f"No handler for message type: {message_type}")
        return
    try:
        
        await handler(message)
    
    except Exception as ex:    
        logger.exception(f"Error handling message of type {message_type}: {ex}")
        raise