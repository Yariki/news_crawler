from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class RobotSite:
    url: str
    content: str
    can_fetch: bool
    crawl_delay: int | None
    request_rate: int | None
    last_checked: datetime = datetime.now(timezone.utc)
