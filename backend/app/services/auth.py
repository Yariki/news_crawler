from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.rbac import Permission, ROLE_PERMISSIONS, Role
from app.models.auth_session import AuthSession
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.models.user_permission_override import UserPermissionOverride


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    rounds = 390000
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), rounds)
    return f"pbkdf2_sha256${rounds}${salt}${hashed.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, rounds, salt, digest = password_hash.split("$", 3)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(rounds)).hex()
    return hmac.compare_digest(candidate, digest)


def validate_password_strength(password: str) -> None:
    if len(password) < 10:
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters long")
    if not any(ch.islower() for ch in password):
        raise HTTPException(status_code=400, detail="Password must include a lowercase letter")
    if not any(ch.isupper() for ch in password):
        raise HTTPException(status_code=400, detail="Password must include an uppercase letter")
    if not any(ch.isdigit() for ch in password):
        raise HTTPException(status_code=400, detail="Password must include a digit")
    if not any(not ch.isalnum() for ch in password):
        raise HTTPException(status_code=400, detail="Password must include a special character")


def get_effective_permissions(user: User) -> set[str]:
    role = Role(user.role)
    permissions = {p.value for p in ROLE_PERMISSIONS[role]}
    for override in user.permission_overrides:
        if override.is_allowed:
            permissions.add(override.permission)
        else:
            permissions.discard(override.permission)
    return permissions


def has_permission(user: User, permission: Permission | str) -> bool:
    value = permission.value if isinstance(permission, Permission) else permission
    return value in get_effective_permissions(user)


def can_access_owner(user: User, owner_id: str | None) -> bool:
    role = Role(user.role)
    if role == Role.ADMIN:
        return True
    if role == Role.SUPER_VIEWER:
        return True
    if owner_id is None:
        return role in {Role.TEAM_LEAD, Role.TEAM_VIEWER}
    if role == Role.TEAM_MEMBER:
        return str(user.id) == str(owner_id)
    return True


def can_mutate_owner(user: User, owner_id: str | None) -> bool:
    role = Role(user.role)
    if role == Role.ADMIN:
        return True
    if role == Role.SUPER_VIEWER:
        return False
    if owner_id is None:
        return role == Role.TEAM_LEAD
    if role == Role.TEAM_MEMBER:
        return str(user.id) == str(owner_id)
    return role == Role.TEAM_LEAD


async def get_user_with_overrides(db: AsyncSession, *, email: str) -> User | None:
    query = (
        select(User)
        .where(User.email == email.lower())
        .options(selectinload(User.permission_overrides))
    )
    return await db.scalar(query)


async def get_user_by_id_with_overrides(db: AsyncSession, user_id: str) -> User | None:
    query = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.permission_overrides))
    )
    return await db.scalar(query)


def _new_token() -> str:
    return secrets.token_urlsafe(48)


async def create_session_tokens(db: AsyncSession, user: User) -> tuple[str, str]:
    access_token = _new_token()
    refresh_token = _new_token()
    now = _utcnow()
    session = AuthSession(
        user_id=user.id,
        access_token_hash=_token_hash(access_token),
        refresh_token_hash=_token_hash(refresh_token),
        access_expires_at=now + timedelta(seconds=settings.access_token_ttl_seconds),
        refresh_expires_at=now + timedelta(seconds=settings.refresh_token_ttl_seconds),
        revoked=False,
    )
    db.add(session)
    await db.commit()
    return access_token, refresh_token


async def find_user_by_access_token(db: AsyncSession, access_token: str) -> User | None:
    now = _utcnow()
    session = await db.scalar(
        select(AuthSession).where(
            AuthSession.access_token_hash == _token_hash(access_token),
            AuthSession.revoked.is_(False),
            AuthSession.access_expires_at > now,
        )
    )
    if not session:
        return None
    return await get_user_by_id_with_overrides(db, str(session.user_id))


async def revoke_by_access_token(db: AsyncSession, access_token: str) -> None:
    session = await db.scalar(select(AuthSession).where(AuthSession.access_token_hash == _token_hash(access_token)))
    if not session:
        return
    session.revoked = True
    await db.commit()


async def rotate_refresh_token(db: AsyncSession, refresh_token: str) -> tuple[User, str, str]:
    now = _utcnow()
    session = await db.scalar(
        select(AuthSession).where(
            AuthSession.refresh_token_hash == _token_hash(refresh_token),
            AuthSession.revoked.is_(False),
            AuthSession.refresh_expires_at > now,
        )
    )
    if not session:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = await get_user_by_id_with_overrides(db, str(session.user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    session.revoked = True
    access_token, new_refresh_token = _new_token(), _new_token()
    new_session = AuthSession(
        user_id=user.id,
        access_token_hash=_token_hash(access_token),
        refresh_token_hash=_token_hash(new_refresh_token),
        access_expires_at=now + timedelta(seconds=settings.access_token_ttl_seconds),
        refresh_expires_at=now + timedelta(seconds=settings.refresh_token_ttl_seconds),
        revoked=False,
    )
    db.add(new_session)
    await db.commit()
    return user, access_token, new_refresh_token


async def create_password_reset_token(db: AsyncSession, user: User) -> str:
    token = _new_token()
    reset = PasswordResetToken(
        user_id=user.id,
        token_hash=_token_hash(token),
        expires_at=_utcnow() + timedelta(seconds=settings.password_reset_token_ttl_seconds),
        used=False,
    )
    db.add(reset)
    await db.commit()
    return token


async def apply_password_reset(db: AsyncSession, token: str, new_password: str) -> None:
    validate_password_strength(new_password)
    now = _utcnow()
    reset = await db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == _token_hash(token),
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > now,
        )
    )
    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = await db.get(User, reset.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user.password_hash = hash_password(new_password)
    user.force_password_change = False
    reset.used = True
    await db.commit()

