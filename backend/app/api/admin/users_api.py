from fastapi import status as HttpStatus, APIRouter, Depends

from app.core.rbac import  RequiredRoles
from app.db.session import DbSession
from app.schemas.role_models import RoleRead
from app.schemas.user_models import AdminChangePassword, UserRead, UserCreate, UserUpdate, UserRoles
from app.services.user_service import UserService

from uuid import UUID

router = APIRouter(
    prefix="/admin/users",
    tags=["admin"],
)


@router.get("", status_code=HttpStatus.HTTP_200_OK, response_model=list[UserRead],
            dependencies=[Depends(RequiredRoles('admin'))])
async def get_users(db: DbSession):
    users = await UserService(db).get_users()
    return users


@router.get("/{user_id}", status_code=HttpStatus.HTTP_200_OK, response_model=UserRead,
            dependencies=[Depends(RequiredRoles('admin'))])
async def get_user(user_id: UUID, db: DbSession):
    user = await UserService(db).get_by_id(user_id)
    return user


@router.post("", status_code=HttpStatus.HTTP_201_CREATED, response_model=UserRead,
             dependencies=[Depends(RequiredRoles('admin'))])
async def create_user(user: UserCreate, db: DbSession):
    new_user = await UserService(db).create_user(user)
    return new_user


@router.put("/{user_id}", status_code=HttpStatus.HTTP_200_OK, response_model=UserRead,
            dependencies=[Depends(RequiredRoles('admin'))])
async def update_user(user_id: UUID, user: UserUpdate, db: DbSession):
    updated_user = await UserService(db).update_user(user_id, user)
    return updated_user

@router.delete("/{user_id}", status_code=HttpStatus.HTTP_204_NO_CONTENT,
            dependencies=[Depends(RequiredRoles('admin'))])
async def delete_user(user_id: UUID, db: DbSession):
    await UserService(db).delete_user(user_id)
    return None

@router.post("/{user_id}/activate", status_code=HttpStatus.HTTP_201_CREATED, response_model=UserRead,
             dependencies=[Depends(RequiredRoles('admin'))])
async def activate_user(user_id: UUID, db: DbSession):
    user = await UserService(db).change_user_activation_status(user_id, True)
    return user

@router.post("/{user_id}/deactivate", status_code=HttpStatus.HTTP_201_CREATED, response_model=UserRead,
             dependencies=[Depends(RequiredRoles('admin'))])
async def deactivate_user(user_id: UUID, db: DbSession):
    user = await UserService(db).change_user_activation_status(user_id, False)
    return user

@router.post("/{user_id}/change-password", status_code=HttpStatus.HTTP_201_CREATED, response_model=UserRead,
             dependencies=[Depends(RequiredRoles('admin'))])
async def change_user_password(user_id: UUID, admin_change_password: AdminChangePassword, db: DbSession):
    user = await UserService(db).change_password(user_id, admin_change_password)
    return user

@router.get("/{user_id}/roles", status_code=HttpStatus.HTTP_200_OK, response_model=list[RoleRead],
            dependencies=[Depends(RequiredRoles('admin'))])
async def get_user_roles(user_id: UUID, db: DbSession):
    roles = await UserService(db).get_user_roles(user_id)
    return roles

@router.post("/{user_id}/roles", status_code=HttpStatus.HTTP_200_OK, response_model=UserRead,
            dependencies=[Depends(RequiredRoles('admin'))])
async def assign_roles(user_id: UUID, roles: UserRoles, db: DbSession):
    user = await UserService(db).assign_roles(user_id, roles.roles_ids)
    return user

@router.delete("/{user_id}/roles/{role_id}", status_code=HttpStatus.HTTP_200_OK, response_model=UserRead,
                dependencies=[Depends(RequiredRoles('admin'))])
async def remove_roles(user_id: UUID, role_id: UUID, db: DbSession):
    user = await UserService(db).remove_roles(user_id, role_id)
    return user
