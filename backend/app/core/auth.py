from typing import Annotated, Any, NoReturn
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from app.core.security import decode_token
from app.db.session import DbSession
from app.models import User
from app.core.config import settings

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
        .where(User.id == user_id)
    )

    result = await db.execute(statement)

    return result.scalars().one_or_none()

async def _authenticate_token(*, token: str, db: DbSession) -> User | None:

    claims = decode_token(token, settings)
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    try:
        user_uuid = UUID(str(user_id))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = await _load_user(user_id=user_uuid, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return user


async def get_current_user(token: OptionalBearerToken, db: DbSession ) -> User | None:

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
