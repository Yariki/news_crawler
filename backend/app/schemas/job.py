from __future__ import annotations

from datetime import datetime

from pydantic import UUID4, BaseModel


class CrawlJobRead(BaseModel):
    id: UUID4
    source_id: UUID4
    status: str
    started_at: datetime
    finished_at: datetime | None
    articles_found: int
    articles_created: int
    error_message: str | None

    model_config = {"from_attributes": True}


