
from pydantic import BaseModel

from app.schemas.role_models import RoleDistribution


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    recent_registrations: int
    role_distributions: list[RoleDistribution]
 