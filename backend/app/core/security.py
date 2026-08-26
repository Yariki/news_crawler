from datetime import datetime, timezone, timedelta
import secrets
from uuid import UUID

from fastapi import HTTPException, status as HttpStatus
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt

from app.core.config import Settings
from app.core.token_rotation import add_new_refreshed_token
from app.schemas.security import TokenType, TokenPair


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def _create_token(*, subject: str, \
                  token_type: TokenType,\
                  ttl: timedelta,\
                  issuer: str,\
                  secret_key:str, \
                  secret_alg: str,\
                  extra_claims: dict | None = None) -> tuple[str,str, datetime]:

    now = datetime.now(timezone.utc)
    expires_at = now + ttl
    jti = secrets.token_urlsafe(32)

    claims = {
        "jti": jti,
        "exp": expires_at,
        "iat": now,
        "iss": issuer,
        "sub": subject,
        "user_id": subject,
        "type": token_type.value,
    }
    if extra_claims is not None:
        claims.update(extra_claims)

    token = jwt.encode(claims, secret_key, algorithm=secret_alg)
    return token, jti, expires_at

async def issue_token_pair(db: AsyncSession, user_id: str, settings: Settings, roles: list[str] | None = None, permissions: list[str] | None = None) -> tuple[TokenPair, str, datetime]:

    access_ttl_ = timedelta(minutes=settings.access_ttl_minutes)
    refresh_ttl_ = timedelta(minutes=settings.refresh_ttl_minutes)

    access_token, _ ,_ = _create_token(
        subject=user_id,
        token_type=TokenType.ACCESS,
        ttl=access_ttl_,
        issuer=settings.issuer,
        secret_key=settings.security_key,
        secret_alg=settings.algorithm,
        extra_claims={
            'roles':roles or  [],
            'permissions': permissions or []
        }
    )
    refresh_token, jti , expires_at = _create_token(
        subject=user_id,
        token_type=TokenType.REFRESH,
        ttl=refresh_ttl_,
        issuer=settings.issuer,
        secret_key=settings.security_key,
        secret_alg=settings.algorithm
    )

    await add_new_refreshed_token(db, jti, UUID(user_id), expires_at)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        access_token_exp=access_ttl_.total_seconds(),
        refresh_token_exp=refresh_ttl_.total_seconds()
    ), jti, expires_at



def decode_token(token: str, settings: Settings) -> dict:
    try:
        claims =  jwt.decode(token, settings.security_key, algorithms=[settings.algorithm])
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    return claims
