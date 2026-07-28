from sqlalchemy import UUID, Boolean, DateTime, ForeignKey, String
from app.db.base import ChangeTrackingMixin, PrimaryIdMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship

class UserRole(ChangeTrackingMixin):
    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"),  nullable=False, primary_key=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"), nullable=False, primary_key=True)

    def __repr__(self) -> str:
        return f"<UserRole user_id={self.user_id}, role_id={self.role_id}>"
    