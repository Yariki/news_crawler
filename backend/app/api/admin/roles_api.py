from fastapi import status as HttpStatus, APIRouter, Depends

from app.core.rbac import  RequiredRoles
from app.db.session import DbSession
from app.schemas.role_models import RoleCreateUpdate, RoleRead, PermissionCreateUpdate

from app.schemas.user_models import UserRead
from app.services.roles_service import RolePermissionService

from uuid import UUID

router = APIRouter(
    prefix="/admin/roles",
    tags=["admin"],
)

@router.get("", 
            response_model=list[RoleRead], 
            status_code=HttpStatus.HTTP_200_OK, 
            dependencies=[Depends(RequiredRoles("admin"))])
async def get_roles(db_session: DbSession):
    roles = await RolePermissionService(db_session).get_roles()
    return roles

@router.get("/{resource_id}",
            response_model=RoleRead, 
            status_code=HttpStatus.HTTP_200_OK, 
            dependencies=[Depends(RequiredRoles("admin"))])
async def get_role_by_id(resource_id: UUID, db_session: DbSession):
    role = await RolePermissionService(db_session).get_role_by_id(resource_id)
    return role


@router.post("",
            response_model=RoleRead,
            status_code=HttpStatus.HTTP_201_CREATED,
            dependencies=[Depends(RequiredRoles("admin"))])
async def create_role(role_data: RoleCreateUpdate, db_session: DbSession):
    role = await RolePermissionService(db_session).create_role(role_data)
    return role

@router.put("/{resource_id}",
            response_model=RoleRead,
            status_code=HttpStatus.HTTP_200_OK,
            dependencies=[Depends(RequiredRoles("admin"))])
async def update_role(resource_id: UUID, role_data: RoleCreateUpdate, db_session: DbSession):
    result = await RolePermissionService(db_session).update_role(resource_id, role_data)
    return result


@router.delete("/{resource_id}",
            status_code=HttpStatus.HTTP_204_NO_CONTENT,
            dependencies=[Depends(RequiredRoles("admin"))])
async def delete_role(resource_id: UUID, db_session: DbSession):
    await RolePermissionService(db_session).delete_role(resource_id)
    return {"detail": "Role deleted successfully."}

@router.get("/{resource_id}/permissions",
            response_model=None,
            status_code=HttpStatus.HTTP_201_CREATED,
            dependencies=[Depends(RequiredRoles("admin"))])
async def get_role_permissions(resource_id: UUID, permission: PermissionCreateUpdate, db_session: DbSession):
    await RolePermissionService(db_session).add_permission_to_role(resource_id, permission)
    return {"detail": "Permission added to role successfully."}

@router.post("/{resource_id}/permissions",
            response_model=None,
            status_code=HttpStatus.HTTP_201_CREATED,
            dependencies=[Depends(RequiredRoles("admin"))])
async def add_permission_to_role(resource_id: UUID, permission: PermissionCreateUpdate, db_session: DbSession):
    await RolePermissionService(db_session).add_permission_to_role(resource_id, permission)
    return {"detail": "Permission added to role successfully."}
    
    
@router.delete("/{resource_id}/permissions/{permission_id}",
            response_model=None,
            status_code=HttpStatus.HTTP_204_NO_CONTENT,
            dependencies=[Depends(RequiredRoles("admin"))])
async def remove_permission_from_role(resource_id: UUID, permission_id: UUID, db_session: DbSession):
    await RolePermissionService(db_session).remove_permission_from_role(resource_id, permission_id)
    return {"detail": "Permission removed from role successfully."}


@router.get("/{resource_id}/users",
            response_model=list[UserRead],
            status_code=HttpStatus.HTTP_200_OK,
            dependencies=[Depends(RequiredRoles("admin"))])
async def get_role_users(resource_id: UUID, db_session: DbSession):
    users = await RolePermissionService(db_session).get_users_for_role(resource_id)
    return users
    