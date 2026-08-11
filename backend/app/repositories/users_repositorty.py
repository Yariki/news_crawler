from fastapi import HTTPException, status as HttpStatus
from sqlalchemy import select

from app.db.session import DbSession
from app.models import User
from app.schemas.user_models import UserCreate
from uuid import UUID


class UserRepository:
    def __init__(self, db: DbSession):
        self._db = db

    async def get_users(self) -> list[User]:
        query = (
            select(User)
            .where(~User.is_delete)
            .order_by(User.created_at.desc())
        )

        result = await self._db.scalars(query)

        return list(result)

    async def get_user_by_id(self, user_id) -> User:
        query = (
            select(User)
            .where(User.id == user_id)
            .where(~User.is_delete)
        )

        result = await self._db.scalar(query)

        return result

    async def create_user(self, new_user: User) -> User:
        self._db.add(new_user)
        await self._db.refresh(new_user)

        return new_user

    async def update_user(self,updated_user: User) -> User:
        self._db.add(updated_user)
        await self._db.refresh(updated_user)

        return updated_user

    async def delete_user(self, user_id: UUID) -> None:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="User not found")
        user.is_delete = True
        self._db.add(user)
        await self._db.refresh(user)
