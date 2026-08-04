from datetime import datetime, timezone

from fastapi import APIRouter, status as HttpStatus, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, issue_token_pair, decode_token
from app.core.token_rotation import TokenReusedException, get_active_token
from app.models import User
from app.db.session import get_db
from app.models.issued_refresh_token import IssuedRefreshTokenStatus
from app.schemas.security import LogoutRequest, LoginRequest, TokenPair, RefreshRequest, TokenType
from app.core.config import settings
from app.schemas.user_models import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(
    prefix='/auth',
    tags=['Auth']
)

@router.post('/register', status_code=HttpStatus.HTTP_201_CREATED, response_model=UserRead)
async def register(register_request: UserCreate, db: AsyncSession = Depends(get_db)):
    """Endpoint to register a new user."""
    new_user = await UserService(db).create_user(register_request)

    return new_user

@router.post('/login', status_code=HttpStatus.HTTP_200_OK, response_model=TokenPair)
async def login(login_request: LoginRequest, db: AsyncSession = Depends(get_db)):

    existing_user = await db.scalar(
        select(User)
            .where(User.email == login_request.email)
    )

    if not existing_user:
        raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    if not existing_user.is_active or not verify_password(login_request.password, existing_user.hashed_password):
        raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    token_pair, _, _ = await issue_token_pair(db, str(existing_user.id), settings)

    await db.commit()

    return token_pair


@router.post('/refresh', status_code=HttpStatus.HTTP_200_OK, response_model=TokenPair)
async def refresh_token(refresh_request: RefreshRequest, db: AsyncSession = Depends(get_db)):

    claims = decode_token(refresh_request.refresh_token, settings)
    
    jti = validate_claims(claims)
    
    try:
        active_refresh_token = await get_active_token(db, jti)
    except TokenReusedException as exc:
        raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    user_id = claims.get("user_id")
    if not user_id:
        raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    existing_user = await db.scalar(
        select(User).where(User.id == user_id)
    )
    if not existing_user or not existing_user.is_active:
        raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    token_pair, jti, _ = await issue_token_pair(db, str(existing_user.id), settings)

    active_refresh_token.status = IssuedRefreshTokenStatus.ROTATED.value
    active_refresh_token.replaced_by_jti = jti
    active_refresh_token.terminal_at = datetime.now(timezone.utc)
    db.add(active_refresh_token)
    await db.commit()
    
    return token_pair

@router.post('/logout', status_code=HttpStatus.HTTP_200_OK)
async def logout(logout_request: LogoutRequest, db: AsyncSession = Depends(get_db)):
    
    claims = decode_token(logout_request.refresh_token, settings)
    if not claims:
        raise HTTPException(status_code=HttpStatus.HTTP_400_BAD_REQUEST, detail="Invalid refresh token.")
    
    jti = validate_claims(claims)
    
    try:
        active_refresh_token = await get_active_token(db, jti)
    except TokenReusedException as exc:
        raise HTTPException(status_code=HttpStatus.HTTP_400_BAD_REQUEST, detail="Refresh token has been reused or is not active.")
    
    active_refresh_token.status = IssuedRefreshTokenStatus.REVOKED.value
    active_refresh_token.terminal_at = datetime.now(timezone.utc)
    db.add(active_refresh_token)
    await db.commit()
    
    return {"message": "Logged out successfully."}

def validate_claims(claims: dict) -> str:
    if not claims:
        raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    
    token_type = claims.get("type")
    if token_type not in [TokenType.ACCESS, TokenType.REFRESH]:
        raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    
    expires_at = claims.get("exp")
    if not expires_at or datetime.fromtimestamp(expires_at, tz=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    
    jti = claims.get("jti")
    if not jti:
        raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    return jti


