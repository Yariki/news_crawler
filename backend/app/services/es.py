from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from elasticsearch import Elasticsearch

from app.core.config import settings

INDEX_NAME = "articles*"
COMMON_TEMPLATE_NAME = "articles-common"
ARTICLES_LANG_TEMPLATE = "articles-lang-"
COMMON_ALIAS="articles-aliases"
COMMON_INDEX_LANG_NAME="articles-template-"


LANGUAGE_INDEX = {
    "en": "articles-en",
    "uk": "articles-uk",
    "de": "articles-de",
    "fr": "articles-fr",
    "es": "articles-es",
    "zh": "articles-zh",
    "ja": "articles-ja",
    "ar": "articles-ar",
    "pt": "articles-pt",
    "hi": "articles-hi",
    "ru": "articles-ru",
    "other": "articles-other",
}

def get_index(lang: str) -> str:
    return LANGUAGE_INDEX[lang] if lang in LANGUAGE_INDEX else "articles-other"

@dataclass(frozen=True)
class LanguageConfig:
    code: str
    name: str
    analyzer: str


LANGUAGES = {
    "en": LanguageConfig("en", "English", "english"),
    "uk": LanguageConfig("uk", "Ukrainian", "ukrainian"),
    "de": LanguageConfig("de", "German", "german"),
    "fr": LanguageConfig("fr", "French", "french"),
    "es": LanguageConfig("es", "Spanish", "spanish"),
    "zh": LanguageConfig("zh", "Chinese", "smartcn"),
    "ja": LanguageConfig("ja", "Japanese", "kuromoji"),
    "ar": LanguageConfig("ar", "Arabic", "arabic"),
    "pt": LanguageConfig("pt", "Portuguese", "portuguese"),
    "hi": LanguageConfig("hi", "Hindi", "hindi"),
    "ru": LanguageConfig("ru", "Russian", "russian"),
    "other": LanguageConfig("other", "Other", "standard"),
}


class ElasticService:
    def __init__(self) -> None:
        self.client = Elasticsearch(settings.elasticsearch_url)

    def _create_common_component_template(self, es: Elasticsearch) -> None:
        """Create the common component template."""
        if es.cluster.exists_component_template(name=COMMON_TEMPLATE_NAME):
            return;

        es.cluster.put_component_template(
            name=COMMON_TEMPLATE_NAME,
            template={
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                },
                "mappings": {
                    "dynamic": "strict",
                    "properties": {
                        "article_id": {"type": "text"},
                        "source_id": {"type": "text"},
                        "source_name": {"type": "keyword"},
                        "published_at": {
                            "type": "date",
                            "format": "strict_date_optional_time||epoch_millis",
                        },
                        "url": {"type": "keyword"},
                        "language": {"type": "keyword"},
                        "is_alert": {"type": "boolean"},
                        "owner_id": {"type": "text"},
                    },
                },
            },
        )

    def _create_lang_component_template(self, es: Elasticsearch, lang: str, analyzer: str) -> None:
        """Create the common component template for specific language."""
        name = f"{ARTICLES_LANG_TEMPLATE}{lang}"
        if es.cluster.exists_component_template(name=name):
            return

        es.cluster.put_component_template(
            name=name,
            template={
                "mappings": {
                    "properties": {
                        "title": {
                            "type": "text",
                            "analyzer": analyzer,
                        },
                        "content_text": {
                            "type": "text",
                            "analyzer": analyzer,
                        },
                        "matched_keywords": {
                            "type": "text",
                            "analyzer": analyzer,
                        },
                    },
                },
            },
        )

    def _create_alias_component_template(self, es: Elasticsearch) -> None:
        """Create common alias component template."""
        if es.cluster.exists_component_template(name=COMMON_ALIAS):
            return;

        es.cluster.put_component_template(
            name=COMMON_ALIAS,
            template={
                "aliases": {
                    "articles-all": {},
                },
            },
        )

    def _create_lang_index_template(self, es: Elasticsearch, lang: str) -> None:
        """create index template for specific language."""
        name = f"{COMMON_INDEX_LANG_NAME}{lang}"

        if es.indices.exists_index_template(name=name):
            return

        es.indices.put_index_template(
            name=name,
            index_patterns=[
                f"articles-{lang}*",
            ],
            priority=100,
            composed_of=[
                COMMON_TEMPLATE_NAME,
                COMMON_ALIAS,
                f"{ARTICLES_LANG_TEMPLATE}{lang}",
            ],
        )

    def _create_language_index(self, es: Elasticsearch, index_name:str) -> None:

        if es.indices.exists(index=index_name):
            return

        es.indices.create(
            index=index_name,
        )

    def _ensure_infrastructure_exists(self) -> None:
        # Components first
        self._create_common_component_template(self.client)
        self._create_alias_component_template(self.client)
        for key, config in LANGUAGES.items():
            self._create_lang_component_template(self.client, key, config.analyzer)

        # Index template second
        for key, _ in LANGUAGES.items():
            self._create_lang_index_template(self.client, key)

        # Physical index last
        for key, index_name in LANGUAGE_INDEX.items():
            self._create_language_index(self.client, index_name)


    async def ensure_infrastructure(self) -> None:
        await asyncio.to_thread(self._ensure_infrastructure_exists)

    async def index_article(self, payload: dict) -> None:

        lang = payload.get("language", "other")
        index_name = get_index(lang)

        await asyncio.to_thread(
            self.client.index,
            index=index_name,
            id=str(payload["article_id"]),
            document=payload,
        )

    async def search(self, query: str, owner_id: str | None = None) -> dict[str, Any]:
        es_query: dict = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "content_text"],
                            "fuzziness": "AUTO",
                            "prefix_length": 1,
                            "max_expansions": 50,
                            "fuzzy_transpositions": True,
                        }
                    }
                ],
                "filter": [],
            }
        }

        if owner_id:
            # Support both explicit keyword mappings and legacy text mapping.
            es_query["bool"]["filter"].append(
                {
                    "bool": {
                        "should": [
                            {"term": {"owner_id.keyword": owner_id}},
                            {"term": {"owner_id": owner_id}},
                            {"match_phrase": {"owner_id": owner_id}},
                        ],
                        "minimum_should_match": 1,
                    }
                }
            )

        return await asyncio.to_thread(
            self.client.search,
            index=INDEX_NAME,
            query=es_query,
            size=50,
        )

    async def count(self) -> int | None:
        try:
            response = await asyncio.to_thread(self.client.count, index=INDEX_NAME)
            return int(response["count"])
        except Exception:
            return None
