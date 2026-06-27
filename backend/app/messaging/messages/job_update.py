from dataclasses import dataclass
from uuid import UUID

from app.messaging.messages.base import BaseMessage, MessageTypes

@dataclass
class JobUpdateMessage(BaseMessage):
    """Message class for job update messages."""
    job_id: UUID
    status: str
    articles_found: int
    articles_created: int
    error_message: str
    started_at: str
    finished_at: str
    source_id: UUID | None = None

    def __init__(self, job_id: UUID, status: str, articles_found: int, articles_created: int, error_message: str, started_at: str, finished_at: str, source_id: UUID | None = None, id: UUID | None = None, type: MessageTypes | None = None):
        super().__init__(id=id,type=MessageTypes.JOB_UPDATE)
        self.job_id = job_id
        self.status = status
        self.articles_found = articles_found
        self.articles_created = articles_created
        self.error_message = error_message
        self.started_at = started_at
        self.finished_at = finished_at
        self.source_id = source_id