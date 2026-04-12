from enum import IntEnum

class Status(IntEnum):
    """Enum representing the status of a task."""
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3
    WAITING = 4
    CANCELED = 5
