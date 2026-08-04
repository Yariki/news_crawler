from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issued_refresh_token import IssuedRefreshToken, IssuedRefreshTokenStatus

class TokenReusedException(Exception):
    """Throw when you find that token with status not Active"""

async def add_new_refreshed_token(db: AsyncSession, jti: str, user_id: UUID, expires_at: datetime):
    new_token = IssuedRefreshToken(
        jti=jti,
        user_id=user_id,
        status=IssuedRefreshTokenStatus.ACTIVE.value,
        issued_at=datetime.now(timezone.utc),
        expires_at=expires_at,
        terminal_at=None,
        replaced_by_jti=None
    )
    db.add(new_token)
    return new_token

async def get_active_token(db: AsyncSession, jti: str) -> IssuedRefreshToken:

    issued_refresh_token = await db.get(IssuedRefreshToken, jti)


    if not issued_refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")
    
    if issued_refresh_token.status != IssuedRefreshTokenStatus.ACTIVE.value:
        raise TokenReusedException("Refresh token has been reused or is not active")
    
    if issued_refresh_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token has expired")

    return issued_refresh_token

async def mark_token_as_revoked(db: AsyncSession, jti: str, replaced_by_jti: str):
    issued_refresh_token = await db.get(IssuedRefreshToken, jti)
    if not issued_refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")
    
    issued_refresh_token.status = IssuedRefreshTokenStatus.REVOKED.value
    issued_refresh_token.replaced_by_jti = replaced_by_jti
    issued_refresh_token.terminal_at = datetime.now(timezone.utc)

    db.add(issued_refresh_token)
    await db.commit()
    await db.refresh(issued_refresh_token)
    return issued_refresh_token
