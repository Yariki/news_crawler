

import datetime
from uuid import UUID
from sqlalchemy import JSON, DateTime, Integer, String, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PrimaryIdMixin
from app.models.outbox_status import OutboxStatus


class OutboxEvent(PrimaryIdMixin, Base):
    """Model representing an outbox event."""
    __tablename__ = "outbox_events"
    
    __table_args__ = (
        
    )
    
    aggregate_id: Mapped[UUID] = mapped_column(nullable=False)
    event_type: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(Integer, nullable=False, default=OutboxStatus.PENDING.value)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    

