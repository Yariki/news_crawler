
from enum import IntEnum


class OutboxEventType(IntEnum):
    """Enum representing the type of an outbox event."""
    ARTICLE_INDEX = 0
    KEYWORDS_MATCH = 1
    
