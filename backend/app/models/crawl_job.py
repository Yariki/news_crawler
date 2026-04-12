from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import PrimaryIdMixin
from app.models.status import Status


class CrawlJob(PrimaryIdMixin):
    """CrawlJob model representing a single crawl execution for a source."""
    __tablename__ = "crawl_jobs"

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[Status] = mapped_column(Integer, nullable=False, default=Status.WAITING.value)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    articles_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    articles_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    source = relationship("Source", back_populates="jobs")
