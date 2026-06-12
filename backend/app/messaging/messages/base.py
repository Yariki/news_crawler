
from dataclasses import dataclass, fields
from enum import Enum, unique
from typing import Type
from uuid import UUID

@unique
class MessageTypes(str,Enum):
    """Enum for message types."""
    JOB_UPDATE = "JOB_UPDATE"


@dataclass
class BaseMessage:
    """Base class for messages."""
    id: UUID
    type: MessageTypes


def convert_dict_to_message(message: dict, cls: Type[BaseMessage]) -> BaseMessage:
    
    set_field = {field.name for field in fields(cls)}
    filtered_message = {key: value for key, value in message.items() if key in set_field}
    return cls(**filtered_message)
