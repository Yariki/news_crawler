from sqlalchemy import UUID, ForeignKey
from app.db.base import AssociationChangeTrackingMixin
from sqlalchemy.orm import Mapped, mapped_column

class UserRole(AssociationChangeTrackingMixin):
    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"),  nullable=False, primary_key=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"), nullable=False, primary_key=True)

    def __repr__(self) -> str:
        return f"<UserRole user_id={self.user_id}, role_id={self.role_id}>"
    