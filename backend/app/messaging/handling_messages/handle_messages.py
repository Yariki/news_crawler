import logging
from typing import Any

from app.messaging.messages.job_update import JobUpdateMessage
from app.messaging.messages.keywords_match import KeywordsMatchMessage

from ...messaging.messages.base import MessageTypes
from .job_update_message_handler import job_update_message_handler
from .keyword_match_message_handler import keyword_match_message_handler

logger = logging.getLogger(__name__)


HANDLERS = {
    MessageTypes.JOB_UPDATE: job_update_message_handler,
    MessageTypes.KEYWORDS_MATCH: keyword_match_message_handler,
}

TYPES = {
    MessageTypes.JOB_UPDATE: JobUpdateMessage,
    MessageTypes.KEYWORDS_MATCH: KeywordsMatchMessage,
}


async def handle_message(raw_payload: dict[str, Any]) -> None:
    """Dispatch an incoming RabbitMQ message to its type-specific handler."""
    logger.debug("Received message: %s", raw_payload)
    try:
        message_type = raw_payload.get("type") if "type" in raw_payload else None
        parsed_message_type = MessageTypes(message_type) if message_type else None
        message_arg_type = TYPES.get(parsed_message_type) if parsed_message_type else None
        
        if not message_arg_type:
            logger.warning("No message class for message type: %s", message_type)
            return
        
        message =  message_arg_type(**raw_payload)
        
        handler = HANDLERS.get(parsed_message_type) if parsed_message_type else None
        if not handler:
            logger.warning("No handler for message type: %s", message_type)
            return
    
        await handler(message)
    except Exception as  ex:
        logger.exception("Error handling message of type %s, %s", message_type, ex)
        raise
