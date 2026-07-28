
from sqlalchemy import UUID, Boolean, DateTime, ForeignKey, String
from datetime import datetime

from traitlets import Integer
from app.db.base import ChangeTrackingMixin, PrimaryIdMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship

class RolePermission(ChangeTrackingMixin):
    __tablename__ = "role_permissions"

    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"),  nullable=False, primary_key=True)
    permission_id: Mapped[UUID] = mapped_column(ForeignKey("permissions.id"), nullable=False, primary_key=True)

    def __repr__(self) -> str:
        return f"<RolePermission role_id={self.role_id}, permission_id={self.permission_id}>"
