
from app.db.session import AsyncSession
from sqlalchemy import select
from app.models import Source
from uuid import UUID
import json


async def export_sources(db: AsyncSession, owner_id: UUID) -> bytes:
    query = (
        select(Source.base_url, Source.name, Source.language, Source.source_type, Source.crawler_key, Source.scrape_interval_minutes, Source.is_enabled)
        .where(Source.owner_id == owner_id)
    )
    result = (await db.execute(query)).mappings().all()

    return json.dumps([dict(row) for row in result]).encode('utf-8')
    