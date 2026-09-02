from fastapi import status as HttpStatus, APIRouter, Depends

from app.core.rbac import RequiredRoles
from app.db.session import DbSession
from app.schemas.role_models import PermissionRead, RoleCreateUpdate, RoleRead, PermissionCreateUpdate

from app.schemas.user_models import UserRead
from app.services.roles_service import RolePermissionService

from uuid import UUID

router = APIRouter(
    prefix="/admin/permissions",
    tags=["admin"],
)

@router.get("/",
            response_model=list[PermissionRead],
            status_code=HttpStatus.HTTP_200_OK,
            dependencies=[Depends(RequiredRoles("admin"))])
async def get_permissions(db_session: DbSession):
    permissions = await RolePermissionService(db_session).get_permissions()
    return permissions
