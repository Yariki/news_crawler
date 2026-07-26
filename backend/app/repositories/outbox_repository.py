
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox_event import OutboxEvent
from app.models.outbox_status import OutboxStatus


class OutboxRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    def enqueue(self, aggregate_id: UUID, event_type: int, payload: dict) -> OutboxEvent:
        """Enqueue a new outbox event."""
        now = datetime.now(timezone.utc)
        new_event = OutboxEvent(
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload_json=payload,
            status=OutboxStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            next_attempt_at=datetime.now(timezone.utc)
        )
        self._db.add(new_event)
        return new_event
    
    
    async def claim_batch(self, limit: int = 50) -> list[OutboxEvent]:
        """Returns the list of pending outbox events that are due for processing, up to the specified limit. The events are locked for processing to prevent concurrent claims."""
        now = datetime.now(timezone.utc)
        query = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxStatus.PENDING)
            .where(OutboxEvent.next_attempt_at <= now)
            .order_by(OutboxEvent.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        
        result = await self._db.execute(query)
        events = list(result.scalars().all())
        return events
        
    def mark_as_processed(self, event: OutboxEvent) -> None:
        """Mark the given outbox event as processed."""
        event.status = OutboxStatus.PROCESSED
        event.processed_at = datetime.now(timezone.utc)

    def mark_as_failed(self, event: OutboxEvent, retry_delay: int, max_attempts: int,  error_message: str) -> None:
        """Mark the given outbox event as failed and schedule it for a retry after the specified delay."""
        event.attempts += 1
        event.last_error = error_message[:1000]
        if event.attempts >= max_attempts:
            event.status = OutboxStatus.DEAD_LETTER
            return
        event.next_attempt_at = datetime.now(timezone.utc) + timedelta(
                seconds=retry_delay * (2 ** (event.attempts - 1))
            )
    