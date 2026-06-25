
from dataclasses import dataclass, fields
from enum import Enum, unique
from typing import Type
from uuid import UUID

@unique
class MessageTypes(str,Enum):
    """Enum for message types."""
    JOB_UPDATE = "JOB_UPDATE"
    KEYWORDS_MATCH = "KEYWORDS_MATCH"


@dataclass
class BaseMessage:
    """Base class for messages."""
    id: UUID
    type: MessageTypes

    def __init__(self, type: MessageTypes):
        self.id = UUID(int=UUID.bytes_le.__hash__(self))
        self.type = type


def convert_dict_to_message(message: dict, cls: Type[BaseMessage]) -> BaseMessage:
    
    set_field = {field.name for field in fields(cls)}
    filtered_message = {key: value for key, value in message.items() if key in set_field}
    return cls(**filtered_message)

def to_dict(message: BaseMessage) -> dict:
    """Convert a message to a dictionary."""
    return {field.name: getattr(message, field.name) for field in fields(message)}
