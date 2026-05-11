from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, hash_refresh_token, verify_password
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.db.scalar(select(User).where(User.email == email.lower().strip()))
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user

    async def get_user_roles(self, user_id: UUID) -> list[str]:
        result = await self.db.scalars(
            select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id).order_by(Role.name)
        )
        return list(result.all())

    async def get_user_permissions(self, user_id: UUID) -> list[str]:
        result = await self.db.scalars(
            select(RolePermission.permission)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .order_by(RolePermission.permission)
        )
        return sorted(set(result.all()))

    async def issue_tokens(self, user: User) -> dict:
        roles = await self.get_user_roles(user.id)
        access_token = create_access_token(str(user.id), roles, settings.access_token_expire_minutes)
        refresh = await self._create_refresh_token(user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh["token"],
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    async def rotate_refresh_token(self, raw_refresh_token: str) -> dict:
        token_hash = hash_refresh_token(raw_refresh_token)
        token = await self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        if token.expires_at <= datetime.now(timezone.utc):
            await self._revoke_family(token.family_id)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
        if token.revoked_at is not None:
            await self._revoke_family(token.family_id)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

        if token.replaced_by_token_id is not None:
            await self._revoke_family(token.family_id)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token reuse detected")

        user = await self.db.get(User, token.user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")

        new_token = await self._create_refresh_token(user.id, family_id=token.family_id, parent_token_id=token.id)
        token.replaced_by_token_id = new_token["id"]
        token.revoked_at = datetime.now(timezone.utc)
        await self.db.commit()

        roles = await self.get_user_roles(user.id)
        access_token = create_access_token(str(user.id), roles, settings.access_token_expire_minutes)
        return {
            "access_token": access_token,
            "refresh_token": new_token["token"],
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    async def revoke_refresh_token(self, raw_refresh_token: str) -> None:
        token_hash = hash_refresh_token(raw_refresh_token)
        token = await self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        if token is None:
            return
        token.revoked_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def _create_refresh_token(self, user_id: UUID, family_id: str | None = None, parent_token_id: UUID | None = None) -> dict:
        raw_token = secrets.token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        family = family_id or secrets.token_hex(16)
        model = RefreshToken(
            user_id=user_id,
            token_hash=hash_refresh_token(raw_token),
            family_id=family,
            parent_token_id=parent_token_id,
            expires_at=expires_at,
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return {"id": model.id, "token": raw_token}

    async def _revoke_family(self, family_id: str) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.db.commit()


class AdminService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_users(self) -> list[User]:
        result = await self.db.scalars(select(User).order_by(User.email))
        return list(result.all())

    async def get_user(self, user_id: UUID) -> User:
        user = await self.db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def create_user(self, email: str, password: str, is_active: bool, role_ids: list[UUID]) -> User:
        normalized_email = email.strip().lower()
        existing = await self.db.scalar(select(User).where(User.email == normalized_email))
        if existing:
            raise HTTPException(status_code=409, detail="User email already exists")
        user = User(email=normalized_email, password_hash=hash_password(password), is_active=is_active)
        self.db.add(user)
        await self.db.flush()
        for role_id in role_ids:
            self.db.add(UserRole(user_id=user.id, role_id=role_id))
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(self, user_id: UUID, is_active: bool | None = None, password: str | None = None) -> User:
        user = await self.get_user(user_id)
        if is_active is not None:
            user.is_active = is_active
        if password:
            user.password_hash = hash_password(password)
            await self.db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: UUID) -> None:
        user = await self.get_user(user_id)
        await self.db.delete(user)
        await self.db.commit()

    async def list_roles(self) -> list[Role]:
        result = await self.db.scalars(select(Role).order_by(Role.name))
        return list(result.all())

    async def get_role(self, role_id: UUID) -> Role:
        role = await self.db.get(Role, role_id)
        if role is None:
            raise HTTPException(status_code=404, detail="Role not found")
        return role

    async def create_role(self, name: str, permissions: list[str]) -> Role:
        normalized_name = name.strip().lower()
        existing = await self.db.scalar(select(Role).where(Role.name == normalized_name))
        if existing:
            raise HTTPException(status_code=409, detail="Role name already exists")
        role = Role(name=normalized_name)
        self.db.add(role)
        await self.db.flush()
        for permission in sorted(set(permissions)):
            self.db.add(RolePermission(role_id=role.id, permission=permission.strip().lower()))
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def update_role(self, role_id: UUID, name: str | None = None, permissions: list[str] | None = None) -> Role:
        role = await self.get_role(role_id)
        if name:
            role.name = name.strip().lower()
        if permissions is not None:
            await self.db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
            for permission in sorted(set(permissions)):
                self.db.add(RolePermission(role_id=role.id, permission=permission.strip().lower()))
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def delete_role(self, role_id: UUID) -> None:
        role = await self.get_role(role_id)
        try:
            await self.db.delete(role)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=409, detail="Role is still assigned")

    async def assign_role(self, user_id: UUID, role_id: UUID) -> None:
        await self.get_user(user_id)
        await self.get_role(role_id)
        existing = await self.db.scalar(select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id))
        if existing:
            return
        self.db.add(UserRole(user_id=user_id, role_id=role_id))
        await self.db.commit()

    async def remove_role(self, user_id: UUID, role_id: UUID) -> None:
        await self.db.execute(delete(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id))
        await self.db.commit()
