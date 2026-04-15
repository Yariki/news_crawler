from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class ScrapedArticle:
    external_id: str
    url: str
    title: str
    author: str | None
    published_at: datetime | None
    content_html: str | None
    content_text: str
    summary: str | None
    language: str
    tags: list[str]
    raw_payload_json: dict
    checksum: str