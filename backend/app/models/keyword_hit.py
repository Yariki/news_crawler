from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import PrimaryIdMixin


class KeywordHit(PrimaryIdMixin):
    """ KeywordHit model representing an instance of a keyword being found in an article. """
    __tablename__ = "keyword_hits"


    keyword: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    article = relationship("Article", back_populates="keyword_hits")
