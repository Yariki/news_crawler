import re
from datetime import datetime, timezone
from typing import Optional, Tuple, override
from uuid import UUID

from sqlalchemy import Result, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Role
from app.models.permission import Permission
from app.models.user import User
from app.schemas.role_models import AssignPermission, PermissionCreateUpdate, PermissionRead, RoleCreateUpdate, RoleRead, RoleDistribution
from app.schemas.user_models import  UserRead
from fastapi import HTTPException, status as HttpStatus



class RolePermissionService:
    def __init__(self, db_session: AsyncSession):
        self._db = db_session

    async def get_role_by_id(self, role_id: UUID) -> Optional[RoleRead]:
        result = await self._db.execute(
            select(Role)
            .where(Role.id == role_id, ~Role.is_delete)
            .options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{role_id}' not found."
            )

        return RoleRead.from_orm(role) if role else None

    async def get_role_by_name(self, name: str) -> Optional[RoleRead]:
        result = await self._db.execute(
            select(Role)
            .where(Role.name == name, ~Role.is_delete)
            .options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()
        return RoleRead.from_orm(role) if role else None

    async def get_roles(self) -> list[RoleRead]:
        result = await self._db.execute(
            select(Role)
            .where(~Role.is_delete)
            .options(selectinload(Role.permissions))
        )
        roles = result.scalars().all()
        return [RoleRead.from_orm(role) for role in roles]
    
    async def get_role_distribution(self) -> list[RoleDistribution]:
        result = await self._db.execute(
            select(Role.name, func.count(User.id))
            .join(Role.users)
            .group_by(Role.name)
        )
        distribution = result.all()
        return [RoleDistribution(role_name=row[0], user_count=row[1]) for row in distribution]

    async def create_role(self, role_data: RoleCreateUpdate) -> RoleRead:

        query = (
            select(Role)
            .where(Role.name == role_data.name)
        )
        role = (await self._db.execute(query)).scalar_one_or_none()
        
        if role and role.is_delete:
            role.is_delete = False
            return RoleRead.from_orm(role)
        elif role and not role.is_delete:
            raise HTTPException(
                status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_data.name}' already exists."
            )

        new_role = Role(
            name=role_data.name,
            description=role_data.description,
            is_system=role_data.is_system,
            is_delete=False,
            created_at=datetime.now(timezone.utc)
        )
        self._db.add(new_role)
        await self._db.commit()
        await self._db.refresh(new_role, attribute_names=["permissions"])
        return RoleRead.from_orm(new_role)

    async def assign_permission_to_role(self, role_id: UUID, permission: AssignPermission) -> PermissionRead:
        result = await self._db.execute(
            select(Permission).where(Permission.id == permission.permission_id)
        )
        permission_obj = result.scalar_one_or_none()

        if not permission_obj:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Permission with ID '{permission.permission_id}' not found."
            )

        role_result = await self._db.execute(
            select(Role).where(Role.id == role_id, ~Role.is_delete).options(selectinload(Role.permissions))
        )
        role = role_result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{role_id}' not found."
            )

        role.permissions.append(permission_obj)
        self._db.add(role)
        await self._db.commit()
        await self._db.refresh(role, attribute_names=["permissions"])
        return PermissionRead.from_orm(permission_obj)

    async def update_role(self, role_id: UUID, role_data: RoleCreateUpdate) -> RoleRead:
        result = await self._db.execute(
            select(Role).where(Role.id == role_id, ~Role.is_delete)
        )
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{role_id}' not found."
            )

        # Check if the new name already exists for a different role
        query = (
            select(Role)
            .where(Role.name == role_data.name, Role.id != role_id, ~Role.is_delete)
        )
        existing_role = (await self._db.execute(query)).scalar_one_or_none()
        if existing_role:
            raise HTTPException(
                status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_data.name}' already exists."
            )

        role.name = role_data.name
        role.description = role_data.description
        role.updated_at = datetime.now(timezone.utc)
        role.is_system = role_data.is_system

        self._db.add(role)
        await self._db.commit()
        await self._db.refresh(role)
        return RoleRead.from_orm(role)

    async def delete_role(self, role_id: UUID) -> None:
        result = await self._db.execute(
            select(Role).where(Role.id == role_id, ~Role.is_delete)
        )
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{role_id}' not found."
            )

        role.is_delete = True
        role.updated_at = datetime.now(timezone.utc)

        self._db.add(role)
        await self._db.commit()


    async def add_permission_to_role(self, role_id: UUID, permission: PermissionCreateUpdate) -> PermissionRead:
        result = await self._db.execute(
            select(Role)
            .where(Role.id == role_id, ~Role.is_delete)
            .options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{role_id}' not found."
            )

        new_permission = Permission(
            name=f"{permission.resource}:{permission.action}:{permission.scope}",
            description=permission.description,
            resource=permission.resource,
            action=permission.action,
            scope=permission.scope,
            created_at=datetime.now(timezone.utc)
        )
        role.permissions.append(new_permission)
        self._db.add(role)
        await self._db.commit()

        return PermissionRead.from_orm(new_permission)


    async def get_role_permissions(self, role_id: UUID) -> list[PermissionRead]:
        result = await self._db.execute(
            select(Role)
            .where(Role.id == role_id, ~Role.is_delete)
            .options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{role_id}' not found."
            )

        return [PermissionRead.from_orm(permission) for permission in role.permissions]


    async def remove_permission_from_role(self, role_id: UUID, permission_id: UUID) -> None:
        result = await self._db.execute(
            select(Role)
            .where(Role.id == role_id, ~Role.is_delete)
            .options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{role_id}' not found."
            )

        permission_to_remove = next((perm for perm in role.permissions if perm.id == permission_id), None)

        if not permission_to_remove:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Permission with ID '{permission_id}' not found in role '{role.name}'."
            )

        role.permissions.remove(permission_to_remove)
        self._db.add(role)
        await self._db.commit()

    async def get_users_for_role(self, role_id: UUID) -> list[UserRead]:
        result: Result[Tuple[Role]] = await self._db.execute(
            select(Role)
            .where(Role.id == role_id, ~Role.is_delete)
            .options(selectinload(Role.users))
        )
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{role_id}' not found."
            )

        return [UserRead.from_orm(user) for user in role.users]
    
    async def get_permissions(self) -> list[PermissionRead]:
        result = await self._db.execute(
            select(Permission)
            .where(~Permission.is_delete)
        )
        permissions = result.scalars().all()
        return [PermissionRead.from_orm(permission) for permission in permissions]
