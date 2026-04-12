from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CrawlJobRead(BaseModel):
    id: str
    source_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    articles_found: int
    articles_created: int
    error_message: str | None

    model_config = {"from_attributes": True}
