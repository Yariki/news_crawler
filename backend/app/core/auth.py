from typing import Annotated, Any, NoReturn
from uuid import UUID

from app.schemas.security import TokenType
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from app.core.security import decode_token
from app.db.session import DbSession
from app.models import User
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

oath2_schemas = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    scheme_name="Bearer",
    auto_error=False,
)

OptionalBearerToken = Annotated[
    str | None,
    Depends(oath2_schemas)]


async def _load_user(*, user_id: UUID, db: DbSession) -> User | None:

    statement = (
        select(User)
        .where(User.id == user_id, User.is_delete.is_(False))
    )

    result = await db.execute(statement)

    return result.scalars().one_or_none()

async def _authenticate_token(*, token: str, db: DbSession) -> User | None:

    claims = decode_token(token, settings)

    type = claims.get("type")
    if type != TokenType.ACCESS:
        logger.warning("Invalid token type: %s", type)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = claims.get("sub")
    if not user_id:
        logger.warning("Missing user_id in token claims")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    try:
        user_uuid = UUID(str(user_id))
    except (TypeError, ValueError):
        logger.warning("Invalid user_id format: %s", user_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = await _load_user(user_id=user_uuid, db=db)
    if not user:
        logger.warning("User not found for user_id or it was deleted: %s", user_uuid)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return user


async def get_current_user(token: OptionalBearerToken, db: DbSession ) -> User | None:
    """Resolve the bearer access token to a database user for protected routes.

    The dependency accepts the optional OAuth2 bearer output so callers can
    customize missing-token behavior elsewhere, but this protected variant
    always raises 401 when no token is present, when JWT validation fails, when
    the subject is not a UUID, or when the user no longer exists.
    """

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = await _authenticate_token(token=token, db=db)
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User | None:

    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return current_user

async def get_optional_user(*, token: OptionalBearerToken, db: DbSession) -> User | None:

    if not token:
        return None

    user = await _authenticate_token(token=token, db=db)
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
