from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Role
from app.schemas.user_models import AdminChangePassword, UserCreate, UserRead, UserUpdate, UserChangePassword
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

    async def get_users(self) -> list[UserRead]:
        query = (
            select(User)
            .where(~User.is_delete)
        )
        result = await self._db.execute(query)
        users = result.scalars().all()
        return [
            UserRead(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_verified=user.is_verified,
                last_login_at=user.last_login_at,
            )
            for user in users
        ]

    async def delete_user(self, user_id: UUID) -> None:
        query = (
            select(User)
            .where(User.id == user_id, ~User.is_delete)
        )
        result = await self._db.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="User not found")

        user.is_delete = True
        await self._db.commit()

    async def change_user_activation_status(self, user_id: UUID, is_active: bool) -> UserRead:
        query = (
            select(User)
            .where(User.id == user_id, ~User.is_delete)
        )
        result = await self._db.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="User not found")

        user.is_active = is_active
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


    async def assign_roles(self, user_id: UUID, roles_ids: list[UUID]) -> UserRead:
        query = (
            select(User)
            .where(User.id == user_id, ~User.is_delete)
            .options(selectinload(User.roles))
        )
        result = await self._db.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="User not found")

        roles = await self._db.execute(
            select(Role).where(Role.id.in_(roles_ids))
        )
        roles = roles.scalars().all()

        existing_role_ids = [role.id for role in user.roles]

        for role in roles:
            if role.id not in existing_role_ids:
                user.roles.append(role)
                existing_role_ids.append(role.id)

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

    async def remove_roles(self, user_id: UUID, role_id: UUID) -> UserRead:

        role = await self._db.scalar(
            select(Role).where(Role.id == role_id)
        )

        if not role:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="Role not found")

        user = await self._db.scalar(
            select(User).where(User.id == user_id, ~User.is_delete).options(
                selectinload(User.roles)
            )
        )

        if not user:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="User not found")
        
        if role not in user.roles:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="Role not assigned to user")
        
        user.roles.remove(role)
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

    async def change_password(self, user_id: UUID, admin_change_password: AdminChangePassword) -> UserRead:
        query = (
            
            select(User)
            .where(User.id == user_id, ~User.is_delete)
        )
        result = await self._db.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="User not found")

        hashed_password = hash_password(admin_change_password.new_password)
        user.hashed_password = hashed_password
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