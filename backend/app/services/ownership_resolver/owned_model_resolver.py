
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import OwnerMixin
from app.db.session import get_db
from app.services.ownership_resolver.interface import OwnershipResolver
from fastapi import HTTPException, status as HttpStatus


class OwnedModelResolver(OwnershipResolver):
    def __init__(self, model: OwnerMixin):
        self._model = model

    @property
    def model(self):
        return self._model

    async def is_owner(self, db: AsyncSession, user_id: UUID, resource_id: UUID) -> bool:
        """
        Resolves the ownership of the model for the given user.
        Returns True if the user owns the model, False otherwise.
        """

        if not hasattr(self._model, "owner_id"):
            raise ValueError(f"Model {self._model.__class__.__name__} does not have an owner_id attribute.")

        stmt = (
            select(self._model)
            .where(self._model.id == resource_id)
        )
        result = await db.scalar(stmt)
        
        if result is None:
            raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail="The resource not found.")

        return result.owner_id == user_id
