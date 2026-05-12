from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPairResponse,
)
from app.services.auth import (
    apply_password_reset,
    create_password_reset_token,
    create_session_tokens,
    get_effective_permissions,
    get_user_with_overrides,
    hash_password,
    revoke_by_access_token,
    rotate_refresh_token,
    validate_password_strength,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPairResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_with_overrides(db, email=payload.email)
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token, refresh_token = await create_session_tokens(db, user)
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_ttl_seconds,
        must_change_password=user.force_password_change,
    )


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    user, access_token, refresh_token = await rotate_refresh_token(db, payload.refresh_token)
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_ttl_seconds,
        must_change_password=user.force_password_change,
    )


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        return {"status": "ok"}
    token = authorization.split(" ", 1)[1].strip()
    if token:
        await revoke_by_access_token(db, token)
    return {"status": "ok"}


@router.get("/me", response_model=MeResponse)
async def me(user: User | None = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return MeResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        team_id=str(user.team_id) if user.team_id else None,
        force_password_change=user.force_password_change,
        permissions=sorted(get_effective_permissions(user)),
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_with_overrides(db, email=payload.email)
    if not user:
        return ForgotPasswordResponse(message="If the email exists, reset instructions were sent")
    token = await create_password_reset_token(db, user)
    if settings.app_mode in {"dev", "test"}:
        return ForgotPasswordResponse(message="Reset token generated", reset_token=token)
    return ForgotPasswordResponse(message="If the email exists, reset instructions were sent")


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await apply_password_reset(db, payload.token, payload.new_password)
    return {"status": "ok"}


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Old password is invalid")
    validate_password_strength(payload.new_password)
    user.password_hash = hash_password(payload.new_password)
    user.force_password_change = False
    await db.commit()
    return {"status": "ok"}

