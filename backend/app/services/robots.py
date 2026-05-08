import datetime

from protego import Protego
from sqlalchemy.ext.asyncio import AsyncSession
import urllib

from app.core.config import settings
from app.dto.robot_site import RobotSite
from app.models.robots import Robot
from app.repositories.robot_repository import RobotRepository

class RobotsService:
    """Service class for managing robot information and interactions with the database."""
    def __init__(self, url: str,  db: AsyncSession):
        self.db = db
        self.url = url
        self.repo = RobotRepository(db)
        self.protego = None


    async def fetch_robot(self):
        robot_site = await self.repo.get_robot_by_url(self.url)
        if not robot_site:
            await self._load_robot()
        else:
            self.protego = Protego.parse(robot_site.content) if robot_site else None
            await self._check_and_send_update_robot(robot_site)


    def can_fetch(self, user_agent: str, url: str) -> bool:
        if not self.protego:
            return True
        return self.protego.can_fetch(user_agent, url)
    

    def crawl_delay(self, user_agent: str) -> int | None:
        if not self.protego:
            return settings.crawl_delay
        return self.protego.crawl_delay(user_agent) if self.protego.crawl_delay(user_agent) is not None else settings.crawl_delay
    
    def request_rate(self, user_agent: str) -> int | None:
        if not self.protego:
            return settings.request_rate
        return self.protego.request_rate(user_agent) if self.protego.request_rate(user_agent) is not None else settings.request_rate

    async def _load_robot(self) -> None:
        robot_url = f"{self.url}/robots.txt"
        response = urllib.request.urlopen(robot_url)
        robots_content = response.read().decode('utf-8')
        self.protego = Protego.parse(robots_content)
        robot = Robot(
            url=robot_url,
            robots_content=robots_content,
            crawl_delay_seconds=self.protego.crawl_delay("*") if self.protego.crawl_delay("*") is not None else settings.crawl_delay,
            requests_per_minute=self.protego.request_rate("*") if self.protego.request_rate("*") is not None else settings.request_rate,
        )
        self.db.add(robot)
        await self.db.commit()

    async def _check_and_send_update_robot(self, robot_site:Robot) -> None:
        period = datetime.now(datetime.timezone.utc) - robot_site.updated_at
        period_in_days = period.total_seconds() / (24 * 3600)
        if period_in_days >= 7:
            await self._load_robot()


















        