from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import PrimaryIdMixin
from app.models.source_type import SourceType


class Source(PrimaryIdMixin):
    """ Source model representing a news source. """
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Integer, nullable=False, default=SourceType.UNKNOWN.value)
    crawler_key: Mapped[str] = mapped_column(String(100), nullable=False, default='default_scraper')
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    scrape_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=1440)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")
    jobs = relationship("CrawlJob", back_populates="source", cascade="all, delete-orphan")
