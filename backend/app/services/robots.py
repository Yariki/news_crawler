from datetime import datetime, timezone
import logging
from urllib.parse import urlsplit

import httpx
from protego import Protego
from sqlalchemy.ext.asyncio import AsyncSession
import urllib

from app.core.config import settings
from app.dto.robot_site import RobotSite
from app.models.robots import Robot
from app.repositories.robot_repository import RobotRepository
from app.utils.html_utils import get_url

logger = logging.getLogger(__name__)


class RobotsService:
    """Service class for managing robot information and interactions with the database."""

    def __init__(self, url: str, db: AsyncSession):
        self.db = db
        self.url = self._robots_url(url)
        self.repo = RobotRepository(db)
        self.protego = None

    async def fetch_robot(self):
        robot_site = await self.repo.get_robot_site_by_url(self.url)
        if not robot_site:
            await self._load_robot()
        else:
            self.protego = Protego.parse(robot_site.content) if robot_site else None
            await self._check_and_update_robot(robot_site)

    def can_fetch(self, user_agent: str, url: str) -> bool:
        if not self.protego:
            return True
        return self.protego.can_fetch(url, user_agent)

    def crawl_delay(self, user_agent: str) -> int | None:
        if not self.protego:
            return settings.crawl_delay
        return (
            self.protego.crawl_delay(user_agent)
            if self.protego.crawl_delay(user_agent) is not None
            else settings.crawl_delay
        )

    def request_rate(self, user_agent: str) -> int | None:
        if not self.protego:
            return settings.request_rate
        return (
            self.protego.request_rate(user_agent)
            if self.protego.request_rate(user_agent) is not None
            else settings.request_rate
        )

    async def _load_robot(self) -> None:
        response = None
        async with  httpx.AsyncClient(
            timeout= 30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; NewsMonitorBot/0.1)"},
        ) as client:
            response = await client.get(self.url)

        if not response:
            logger.warning(f"Failed to fetch robots.txt from {self.url}")
            return
        
        robots_content = response.read().decode("utf-8")
        self.protego = Protego.parse(robots_content)
        robot = await self.repo.get_robot_by_url(self.url)
        if robot:
            robot.robots_content = robots_content
            robot.crawl_delay_seconds = self.crawl_delay("*")
            robot.requests_per_minute = self.request_rate("*")
            robot.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
            return

        robot = Robot(
            url=self.url,
            robots_content=robots_content,
            crawl_delay_seconds=(
                self.protego.crawl_delay("*")
                if self.protego.crawl_delay("*") is not None
                else settings.crawl_delay
            ),
            requests_per_minute=(
                self.protego.request_rate("*")
                if self.protego.request_rate("*") is not None
                else settings.request_rate
            ),
        )
        self.db.add(robot)
        await self.db.commit()

    async def _check_and_update_robot(self, robot_site: RobotSite) -> None:
        period = datetime.now(timezone.utc) - robot_site.last_checked
        period_in_days = period.total_seconds() / (24 * 3600)
        if period_in_days >= 7:
            await self._load_robot()

    def _robots_url(self, url: str) -> str:
        parsed = get_url(url)
        return f"{parsed}/robots.txt"
