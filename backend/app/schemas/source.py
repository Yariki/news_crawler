from __future__ import annotations

from pydantic import BaseModel, HttpUrl, UUID4


class SourceCreateUpdate(BaseModel):
    name: str
    base_url: HttpUrl
    language: str
    source_type: int
    crawler_key: str
    scrape_interval_minutes: int = 1440
    is_enabled: bool = True


class SourceRead(BaseModel):
    id: str
    name: str
    base_url: str
    language: str
    source_type: int
    crawler_key: str
    is_enabled: bool
    scrape_interval_minutes: int

    model_config = {"from_attributes": True}
