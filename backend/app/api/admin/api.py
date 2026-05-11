from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.dependencies.auth import CurrentUser, require_roles
from app.db.session import get_db
from app.models.role_permission import RolePermission
from app.schemas.auth import RoleCreate, RoleRead, RoleUpdate, UserCreate, UserRead, UserRoleAssignRequest, UserUpdate
from app.services.audit import AuditService
from app.services.auth_service import AdminService, AuthService

router = APIRouter(prefix="/admin", tags=["admin"])


async def _serialize_user(db: AsyncSession, user) -> UserRead:
    auth_service = AuthService(db)
    return UserRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        roles=await auth_service.get_user_roles(user.id),
        permissions=await auth_service.get_user_permissions(user.id),
    )


async def _serialize_role(db: AsyncSession, role) -> RoleRead:
    permissions = await db.scalars(
        select(RolePermission.permission).where(RolePermission.role_id == role.id).order_by(RolePermission.permission)
    )
    return RoleRead(id=role.id, name=role.name, permissions=list(permissions.all()))


@router.get("/users", response_model=list[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_roles(["admin"])),
):
    items = await AdminService(db).list_users()
    return [await _serialize_user(db, item) for item in items]


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
):
    user = await AdminService(db).create_user(payload.email, payload.password, payload.is_active, [UUID(str(i)) for i in payload.role_ids])
    await AuditService(db).log("admin.user.create", user_id=current_user.id, details={"target_user_id": str(user.id)})
    return await _serialize_user(db, user)


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
):
    user = await AdminService(db).update_user(user_id, is_active=payload.is_active, password=payload.password)
    await AuditService(db).log("admin.user.update", user_id=current_user.id, details={"target_user_id": str(user.id)})
    return await _serialize_user(db, user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
):
    await AdminService(db).delete_user(user_id)
    await AuditService(db).log("admin.user.delete", user_id=current_user.id, details={"target_user_id": str(user_id)})
    return None


@router.post("/users/{user_id}/roles", status_code=status.HTTP_204_NO_CONTENT)
async def assign_role(
    user_id: UUID,
    payload: UserRoleAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
):
    await AdminService(db).assign_role(user_id, UUID(str(payload.role_id)))
    await AuditService(db).log(
        "admin.user.role.assign",
        user_id=current_user.id,
        details={"target_user_id": str(user_id), "role_id": str(payload.role_id)},
    )
    return None


@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
):
    await AdminService(db).remove_role(user_id, role_id)
    await AuditService(db).log(
        "admin.user.role.remove", user_id=current_user.id, details={"target_user_id": str(user_id), "role_id": str(role_id)}
    )
    return None


@router.get("/roles", response_model=list[RoleRead])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_roles(["admin"])),
):
    roles = await AdminService(db).list_roles()
    return [await _serialize_role(db, role) for role in roles]


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
):
    role = await AdminService(db).create_role(payload.name, payload.permissions)
    await AuditService(db).log("admin.role.create", user_id=current_user.id, details={"role_id": str(role.id)})
    return await _serialize_role(db, role)


@router.patch("/roles/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
):
    role = await AdminService(db).update_role(role_id, name=payload.name, permissions=payload.permissions)
    await AuditService(db).log("admin.role.update", user_id=current_user.id, details={"role_id": str(role.id)})
    return await _serialize_role(db, role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
):
    await AdminService(db).delete_role(role_id)
    await AuditService(db).log("admin.role.delete", user_id=current_user.id, details={"role_id": str(role_id)})
    return None
