
from enum import StrEnum


class OwnedResourceType(StrEnum):
    ARTICLE = "article"
    CRAWL_JOB = "crawl_job"
    KEYWORD_HIT = "keyword_hit"
    MONITORED_KEYWORD = "monitored_keyword"
    OUTBOX_EVENT = "outbox_event"
    SOURCE = "source"
