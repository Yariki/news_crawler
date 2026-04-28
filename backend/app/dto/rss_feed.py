from datetime import datetime


class RssFeed:
    """
    Data Transfer Object (DTO) representing an RSS feed item.
    """
    id: str
    url: str
    title: str
    author: str | None
    published: datetime | None
    content_html: str | None
    content_text: str | None
    summary: str | None
    tags: list[str] | None
    checksum: str
