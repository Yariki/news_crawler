from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import PrimaryIdMixin


class MonitoredKeyword(PrimaryIdMixin):
    """ MonitoredKeyword model representing a keyword that is being monitored for hits in articles. """
    __tablename__ = "monitored_keywords"

    keyword: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
