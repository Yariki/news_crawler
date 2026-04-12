from __future__ import annotations

from pydantic import BaseModel


class DashboardStats(BaseModel):
    sources_total: int
    sources_enabled: int
    articles_total: int
    alerts_total: int
    jobs_total: int
    keywords_total: int
    elasticsearch_document_count: int | None
