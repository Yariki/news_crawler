from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth_rate_limiter import auth_rate_limiter
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=True)


@dataclass
class CurrentUser:
    id: UUID
    email: str
    roles: list[str]
    permissions: list[str]
    is_active: bool


async def auth_rate_limit(request: Request) -> None:
    auth_rate_limiter.check(request)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active")
    auth_service = AuthService(db)
    roles = await auth_service.get_user_roles(user.id)
    permissions = await auth_service.get_user_permissions(user.id)
    return CurrentUser(id=user.id, email=user.email, roles=roles, permissions=permissions, is_active=user.is_active)


def require_roles(required_roles: list[str]):
    async def _dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if any(role in current_user.roles for role in required_roles):
            return current_user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient roles")

    return _dependency
