from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rbac import Permission
from app.db.session import get_db
from app.models.user import User
from app.services.auth import find_user_by_access_token, has_permission


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User | None:
    if not authorization:
        if settings.app_mode == "test":
            return None
        raise HTTPException(status_code=401, detail="Missing authorization token")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization token")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authorization token")
    user = await find_user_by_access_token(db, token)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid authorization token")
    return user


def require_permission(permission: Permission) -> Callable:
    async def _dependency(
        user: User | None = Depends(get_current_user),
    ) -> User | None:
        if user is None:
            if settings.app_mode == "test":
                return None
            raise HTTPException(status_code=401, detail="Unauthorized")
        if not has_permission(user, permission):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return _dependency


def require_non_forced_password_change() -> Callable:
    async def _dependency(
        user: User | None = Depends(get_current_user),
    ) -> User | None:
        if user is None:
            if settings.app_mode == "test":
                return None
            raise HTTPException(status_code=401, detail="Unauthorized")
        if user.force_password_change:
            raise HTTPException(status_code=403, detail="Password change is required")
        return user

    return _dependency

