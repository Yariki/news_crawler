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

owned_resolves_map: dict[OwnedResourceType, tuple[type[OwnershipResolver], tuple[(Any,...)]]] = {
    OwnedResourceType.ARTICLE: (OwnedModelResolver, (Article,)),
    OwnedResourceType.CRAWL_JOB: (OwnedModelResolver, (CrawlJob,)),
    OwnedResourceType.KEYWORD_HIT: (OwnedModelResolver, (KeywordHit,)),
    OwnedResourceType.MONITORED_KEYWORD: (OwnedModelResolver, (MonitoredKeyword,)),
    OwnedResourceType.OUTBOX_EVENT: (OwnedModelResolver, (OutboxEvent,)),
    OwnedResourceType.SOURCE: (OwnedModelResolver, (Source,))
}

def _get_owned_model_resolver(resource_type: OwnedResourceType) -> OwnershipResolver:
    resolver_data = owned_resolves_map.get(resource_type)
    if resolver_data is None:
        raise ValueError(f"No resolver found for resource type: {resource_type}")
    resolver_class, args = resolver_data
    if not issubclass(resolver_class, OwnershipResolver):
        raise TypeError(f"Resolver class {resolver_class} must be a subclass of OwnershipResolver")
    if not isinstance(args, tuple):
        raise TypeError(f"Arguments for resolver class {resolver_class} must be a tuple")
    return resolver_class(*args)

async def is_user_owner_of_resource(user_id: UUID, resource_type: OwnedResourceType, resource_id: UUID, db: AsyncSession) -> bool:
    """
    Check if a user is the owner of a specific resource.

    Args:
        user_id (UUID): The ID of the user.
        resource_type (OwnedResourceType): The type of the resource.
        resource_id (UUID): The ID of the resource.
        db (AsyncSession): The database session.

    Returns:
        bool: True if the user is the owner of the resource, False otherwise.
    """
    resolver = _get_owned_model_resolver(resource_type)
    return await resolver.is_owner(db, user_id, resource_id)



