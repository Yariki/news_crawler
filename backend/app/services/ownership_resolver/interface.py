
from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession


class OwnershipResolver(ABC):

    @abstractmethod
    async def is_owner(self, db:AsyncSession, user_id: UUID, resource_id: UUID) -> bool:
        """Check if the user is the owner of the resource."""
