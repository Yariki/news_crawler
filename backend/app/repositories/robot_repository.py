
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

from app.dto.robot_site import RobotSite
from app.models.robots import Robot

class RobotRepository:
    """Repository class responsible for managing Robot records in the database. It provides methods to add new robots, update existing robots, and retrieve robot information based on URL. This class abstracts away the database interactions related to the Robot model, allowing other parts of the application to work with RobotSite DTOs without needing to know about the underlying database structure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    
    async def add_robot(self, robot_site: RobotSite) -> None:
        """Adds a new robot record to the database based on the provided RobotSite object."""
        robot = Robot(
            url=robot_site.url,
            robots_content=robot_site.content,
            crawl_delay_seconds=robot_site.crawl_delay,
            requests_per_minute=robot_site.request_rate,
            updated_at=robot_site.last_checked
        )
        
        self.db.add(robot)
        await self.db.commit()

    async def update_robot(self, robot_site: RobotSite) -> None:
        """Updates an existing robot record in the database with new data from the provided RobotSite object."""
        result = await self.db.execute(
            select(Robot).where(Robot.url == robot_site.url)
        )
        robot = result.scalar_one_or_none()
        if robot:
            robot.robots_content = robot_site.content
            robot.crawl_delay_seconds = robot_site.crawl_delay if robot_site.crawl_delay is not None else settings.crawl_delay
            robot.requests_per_minute = robot_site.request_rate if robot_site.request_rate is not None else settings.request_rate
            robot.updated_at = robot_site.last_checked
            await self.db.commit()

    async def get_robot_by_url(self, url: str) -> RobotSite | None:
        """Retrieves a robot record from the database based on the provided URL and returns it as a RobotSite object. If no record is found, returns None."""
        result = await self.db.execute(
            select(Robot).where(Robot.url == url)
        )
        robot =  result.scalar_one_or_none()
        if not robot:
            return None
        
        return RobotSite(
            url=robot.url,
            content=robot.robots_content if robot.robots_content else "", 
            crawl_delay=robot.crawl_delay_seconds,
            request_rate=robot.requests_per_minute,
            last_checked=robot.updated_at,
            can_fetch=True
        )
