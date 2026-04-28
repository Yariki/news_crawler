from abc import ABC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import MonitoredKeyword
from app.services.keyword_detector import normalize_keyword


class BaseCrawler(ABC):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_keywords(self) -> list[str]:
        result = await self.db.scalars(
            select(MonitoredKeyword.keyword)
            .where(MonitoredKeyword.is_enabled.is_(True))
            .order_by(MonitoredKeyword.keyword)
        )
        keywords = [normalize_keyword(value) for value in result.all() if value]
        return keywords or settings.default_keywords_list

