from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID

from app.db.base import PrimaryIdMixin


class MonitoredKeyword(PrimaryIdMixin):
    """ MonitoredKeyword model representing a keyword that is being monitored for hits in articles. """
    __tablename__ = "monitored_keywords"
    __table_args__ = (UniqueConstraint("owner_id", "keyword", name="uq_monitored_keywords_owner_keyword"),)

    keyword: Mapped[str] = mapped_column(String(128), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
