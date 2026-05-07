from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import PrimaryIdMixin


class Robot(PrimaryIdMixin):
    """Robot model representing an automated agent that fetches articles from sources."""
    __tablename__ = "robots"

    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    robots_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    crawl_delay_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requests_per_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(
        timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
