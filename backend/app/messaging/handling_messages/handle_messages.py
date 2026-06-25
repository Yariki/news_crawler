import logging
from typing import Any

from ...messaging.messages.base import MessageTypes
from .job_update_message_handler import job_update_message_handler
from .keyword_match_message_handler import keyword_match_message_handler

logger = logging.getLogger(__name__)


HANDLERS = {
    MessageTypes.JOB_UPDATE: job_update_message_handler,
    MessageTypes.KEYWORDS_MATCH: keyword_match_message_handler,
}


async def handle_message(message: dict[str, Any]) -> None:
    """Dispatch an incoming RabbitMQ message to its type-specific handler."""
    logger.debug("Received message: %s", message)
    message_type = message.get("type")

    try:
        parsed_message_type = MessageTypes(message_type) if message_type else None
    except (TypeError, ValueError):
        parsed_message_type = None

    handler = HANDLERS.get(parsed_message_type) if parsed_message_type else None
    if not handler:
        logger.warning("No handler for message type: %s", message_type)
        return

    try:
        await handler(message)
    except Exception:
        logger.exception("Error handling message of type %s", message_type)
        raise
