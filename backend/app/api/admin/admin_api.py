
from fastapi import APIRouter, Depends, status as HttpStatus
from datetime import datetime, timedelta
from app.core.rbac import RequiredRoles
from app.db.session import DbSession
from app.models.user import User
from app.schemas.admins import AdminStats
from sqlalchemy import select, func

from app.services.roles_service import RolePermissionService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get("/stats",  
            response_model=AdminStats,
            status_code=HttpStatus.HTTP_200_OK,
            dependencies=[Depends(RequiredRoles("admin"))])
async def get_admin_stats(db_session: DbSession):
    user_count = await db_session.execute(select(func.count(User.id)))
    active_user_count = await db_session.execute(select(func.count(User.id)).where(User.is_active == True))
    since = datetime.utcnow() - timedelta(days=7)
    new_user_count = await db_session.execute(select(func.count(User.id)).where(User.created_at >= since))
    distribution = await RolePermissionService(db_session).get_role_distribution()
    return AdminStats(
        total_users=user_count.scalar() or 0,
        active_users=active_user_count.scalar() or 0,
        recent_registrations=new_user_count.scalar() or 0,
        role_distributions=distribution
    )
