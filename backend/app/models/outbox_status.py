from enum import IntEnum


class OutboxStatus(IntEnum):
    """Enum representing the status of an outbox message."""
    PENDING = 0
    PROCESSED = 1
    DEAD_LETTER = 2