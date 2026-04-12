from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ArticleRead(BaseModel):
    id: str
    source_id: str
    url: str
    title: str
    author: str | None
    published_at: datetime | None
    fetched_at: datetime
    content_text: str
    summary: str | None
    language: str
    is_alert: bool
    matched_keywords_csv: str | None

    model_config = {"from_attributes": True}


class SearchHit(BaseModel):
    article_id: str
    title: str
    url: str
    published_at: str | None
    source_name: str
    excerpt: str | None
    score: float | None = None
    is_alert: bool = False
