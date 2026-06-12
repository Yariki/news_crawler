

from uuid import UUID

from app.messaging.messages.base import BaseMessage


class JobFinishedMessage(BaseMessage):
    """Message indicating that a job has finished."""
    job_id: UUID
    source_id: UUID