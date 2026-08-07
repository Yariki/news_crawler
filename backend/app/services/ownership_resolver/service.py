from typing import Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Source
from app.models.article import Article
from app.models.crawl_job import CrawlJob
from app.models.keyword_hit import KeywordHit
from app.models.monitored_keyword import MonitoredKeyword
from app.models.outbox_event import OutboxEvent
from app.models.owned_resource_type import OwnedResourceType
from app.services.ownership_resolver.interface import OwnershipResolver
from app.services.ownership_resolver.owned_model_resolver import OwnedModelResolver

owned_resolves_mao: dict[OwnedResourceType, tuple[type[OwnershipResolver], tuple[(Any,...)]]] = {
    OwnedResourceType.ARTICLE: (OwnedModelResolver, (Article,)),
    OwnedResourceType.CRAWL_JOB: (OwnedModelResolver, (CrawlJob,)),
    OwnedResourceType.KEYWORD_HIT: (OwnedModelResolver, (KeywordHit,)),
    OwnedResourceType.MONITOPRED_KEYWORD: (OwnedModelResolver, (MonitoredKeyword,)),
    OwnedResourceType.OUTBOX_EVENT: (OwnedModelResolver, (OutboxEvent,)),
    OwnedResourceType.SOURCE: (OwnedModelResolver, (Source,))
}

def _get_owned_model_resolver(resource_type: OwnedResourceType) -> OwnershipResolver:
    resolver_class, args = owned_resolves_mao.get(resource_type)
    if resolver_class is None:
        raise ValueError(f"No resolver found for resource type: {resource_type}")
    return resolver_class(*args)

async def is_user_owner_of_resource(user_id: UUID, resource_type: OwnedResourceType, resource_id: UUID, db: AsyncSession) -> bool:
    resolver = _get_owned_model_resolver(resource_type)
    return await resolver.is_owner(db, user_id, resource_id)



