from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user, require_non_forced_password_change, require_permission
from app.core.rbac import Permission, Role
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserReadResponse
from app.services.auth import hash_password, validate_password_strength

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserReadResponse,
    dependencies=[Depends(require_non_forced_password_change())],
)
async def create_user(
    payload: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.USER_CREATE)),
):
    if actor is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        new_role = Role(payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid role") from exc

    if Role(actor.role) == Role.ADMIN:
        pass
    elif Role(actor.role) == Role.TEAM_LEAD:
        if new_role not in {Role.TEAM_MEMBER, Role.TEAM_VIEWER}:
            raise HTTPException(status_code=403, detail="Forbidden")
        if payload.team_id and str(actor.team_id) != payload.team_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        raise HTTPException(status_code=403, detail="Forbidden")

    existing = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists")

    validate_password_strength(payload.password)
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=new_role.value,
        team_id=payload.team_id or actor.team_id,
        is_active=True,
        force_password_change=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserReadResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        team_id=str(user.team_id) if user.team_id else None,
        is_active=user.is_active,
        force_password_change=user.force_password_change,
    )


@router.get(
    "",
    response_model=list[UserReadResponse],
    dependencies=[Depends(require_non_forced_password_change())],
)
async def list_users(
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.USER_READ)),
):
    if actor is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    role = Role(actor.role)
    query = select(User).order_by(User.email)
    if role in {Role.TEAM_LEAD, Role.TEAM_VIEWER, Role.TEAM_MEMBER}:
        query = query.where(User.team_id == actor.team_id)
    users = list((await db.scalars(query)).all())
    return [
        UserReadResponse(
            id=str(user.id),
            email=user.email,
            role=user.role,
            team_id=str(user.team_id) if user.team_id else None,
            is_active=user.is_active,
            force_password_change=user.force_password_change,
        )
        for user in users
    ]

