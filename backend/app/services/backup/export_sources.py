
from app.core.rbac import PermissionGranted
from app.db.scope_filter import filter_owned_resources
from app.db.session import AsyncSession
from sqlalchemy import select
from app.models import Source
from uuid import UUID
import json


async def export_sources(db: AsyncSession, owner_id: UUID, access_granted: PermissionGranted) -> bytes:
    query = (
        select(Source.base_url, Source.name, Source.language, Source.source_type, Source.crawler_key, Source.scrape_interval_minutes, Source.is_enabled)
    )
    query = filter_owned_resources(query=query, user_id=owner_id, model=Source, access_control=access_granted)
    result = (await db.execute(query)).mappings().all()

    return json.dumps([dict(row) for row in result]).encode('utf-8')
    