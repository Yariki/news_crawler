from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_models import UserCreate, UserRead, UserUpdate
from app.models.user import User
from app.core.security import hash_password, verify_password
from fastapi import HTTPException, status as HttpStatus

class UserService:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def __is_email_unique(self, email: str ) -> bool:
        query = (
            select(User)
            .where(User.email == email)
        )
        result = await self._db.execute(query)
        user = result.scalar_one_or_none()
        return user is None

    async def __is_username_unique(self, username: str ) -> bool:
        query = (
            select(User)
            .where(User.username == username)
        )
        result = await self._db.execute(query)
        user = result.scalar_one_or_none()
        return user is None

    async def create_user(self, user_create: UserCreate) -> UserRead:

        if not await self.__is_email_unique(user_create.email):
            raise HTTPException(status_code=HttpStatus.HTTP_400_BAD_REQUEST, detail="Email is already in use")

        if not await self.__is_username_unique(user_create.username):
            raise HTTPException(status_code=HttpStatus.HTTP_400_BAD_REQUEST, detail="Username is already in use")

        hashed_password = hash_password(user_create.password)
        user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password,
            is_active=user_create.is_active,
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return UserRead(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login_at=user.last_login_at,
        )

    async def get_by_email(self, email: str) -> UserRead:
        query = (
            select(User)
            .where(User.email == email, ~User.is_delete)
        )
        result = await self._db.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="User not found")
        return UserRead(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login_at=user.last_login_at,
        )

    async def get_by_id(self, user_id: UUID) -> UserRead:
        query = (
            select(User)
            .where(User.id == user_id, ~User.is_delete)
        )
        result = await self._db.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="User not found")
        return UserRead(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login_at=user.last_login_at,
        )

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        query = (
            select(User)
            .where(User.username == username, ~User.is_delete)
        )
        result = await self._db.execute(query)
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=HttpStatus.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        return user

    async def update_user(self, user_id: UUID, userUpdate: UserUpdate) -> UserRead:

        if not await self.__is_email_unique(userUpdate.email):
            raise HTTPException(status_code=HttpStatus.HTTP_400_BAD_REQUEST, detail="Email is already in use")

        if not await self.__is_username_unique(userUpdate.username):
            raise HTTPException(status_code=HttpStatus.HTTP_400_BAD_REQUEST, detail="Username is already in use")

        query = (
            select(User)
            .where(User.id == user_id, ~User.is_delete)
        )
        result = await self._db.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="User not found")

        user.email = userUpdate.email
        user.username = userUpdate.username
        user.is_active = userUpdate.is_active

        await self._db.commit()
        await self._db.refresh(user)
        return UserRead(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login_at=user.last_login_at,
        )

    async def update_last_login_at(self, user_id: UUID) -> UserRead:
        query = (
            select(User)
            .where(User.id == user_id, ~User.is_delete)
        )
        result = await self._db.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="User not found")

        user.last_login_at = datetime.now(timezone.utc)

        await self._db.commit()
        await self._db.refresh(user)
        return UserRead(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login_at=user.last_login_at,
        )
