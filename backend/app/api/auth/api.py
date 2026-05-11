from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.dependencies.auth import CurrentUser, auth_rate_limit, get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.schemas.auth import AuthEventRead, LoginRequest, RefreshRequest, TokenResponse
from app.services.audit import AuditService
from app.services.auth_rate_limiter import auth_rate_limiter
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(auth_rate_limit)])
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        user = await auth_service.authenticate_user(payload.email, payload.password)
    except Exception:
        auth_rate_limiter.register_login_result(request, success=False)
        await AuditService(db).log("auth.login.failed", details={"email": payload.email})
        raise
    auth_rate_limiter.register_login_result(request, success=True)
    tokens = await auth_service.issue_tokens(user)
    await AuditService(db).log("auth.login.success", user_id=user.id)
    return tokens


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(auth_rate_limit)])
async def refresh_tokens(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    tokens = await auth_service.rotate_refresh_token(payload.refresh_token)
    await AuditService(db).log("auth.refresh.success")
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    auth_service = AuthService(db)
    await auth_service.revoke_refresh_token(payload.refresh_token)
    await AuditService(db).log("auth.logout", user_id=current_user.id)
    return None


@router.get("/me")
async def me(db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    auth_service = AuthService(db)
    permissions = await auth_service.get_user_permissions(current_user.id)
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "is_active": current_user.is_active,
        "roles": current_user.roles,
        "permissions": permissions,
    }


@router.get("/monitoring")
async def auth_monitoring(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    recent = await db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(20))
    events = [
        AuthEventRead(action=item.action, details=item.details, created_at=item.created_at).model_dump()
        for item in recent.all()
    ]
    return {"failed_login_abuse": auth_rate_limiter.abuse_snapshot(), "recent_events": events}
