
from dataclasses import dataclass
from uuid import UUID

@dataclass
class BaseMessage:
    """Base class for messages."""
    id: UUID