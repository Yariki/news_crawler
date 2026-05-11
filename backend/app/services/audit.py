from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, action: str, user_id: UUID | None = None, details: dict | None = None) -> None:
        self.db.add(AuditLog(action=action, user_id=user_id, details=details))
        await self.db.commit()
