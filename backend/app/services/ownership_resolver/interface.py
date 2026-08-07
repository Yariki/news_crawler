
from abc import ABC, abstractmethod
from uuid import UUID


class OwnershipResolver(ABC):

    __abstract__ = True

    @abstractmethod
    def is_owner(self, user_id: UUID, resource_id: UUID) -> bool:
        """Check if the user is the owner of the resource."""
