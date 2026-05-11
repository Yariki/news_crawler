from __future__ import annotations

import asyncio

from elasticsearch import Elasticsearch

from app.core.config import settings

INDEX_NAME = "articles"


class ElasticService:
    def __init__(self) -> None:
        self.client = Elasticsearch(settings.elasticsearch_url)

    def _ensure_index_sync(self) -> None:
        if self.client.indices.exists(index=INDEX_NAME):
            return
        self.client.indices.create(
            index=INDEX_NAME,
            mappings={
                "properties": {
                    "article_id": {"type": "text"},
                    "source_id": {"type": "text"},
                    "owner_id": {"type": "keyword"},
                    "source_name": {"type": "keyword"},
                    "title": {"type": "text"},
                    "content_text": {"type": "text"},
                    "published_at": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis",
                    },
                    "url": {"type": "keyword"},
                    "language": {"type": "keyword"},
                    "is_alert": {"type": "boolean"},
                    "matched_keywords": {"type": "keyword"},
                }
            },
        )

    async def ensure_index(self) -> None:
        await asyncio.to_thread(self._ensure_index_sync)

    async def index_article(self, payload: dict) -> None:
        await asyncio.to_thread(
            self.client.index,
            index=INDEX_NAME,
            id=str(payload["article_id"]),
            document=payload,
        )

    async def search(self, query: str, owner_id: str | None = None) -> dict:
        must_query = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content_text"],
                }
            }
        ]
        if owner_id:
            must_query.append({"term": {"owner_id": owner_id}})
        return await asyncio.to_thread(
            self.client.search,
            index=INDEX_NAME,
            query={"bool": {"must": must_query}},
            size=50,
        )

    async def count(self) -> int | None:
        try:
            response = await asyncio.to_thread(self.client.count, index=INDEX_NAME)
            return int(response["count"])
        except Exception:
            return None


elastic_service = ElasticService()
