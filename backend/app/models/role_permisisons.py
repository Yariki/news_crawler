
from sqlalchemy import UUID, ForeignKey
from app.db.base import AssociationChangeTrackingMixin
from sqlalchemy.orm import Mapped, mapped_column

class RolePermission(AssociationChangeTrackingMixin):
    __tablename__ = "role_permissions"

    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"),  nullable=False, primary_key=True)
    permission_id: Mapped[UUID] = mapped_column(ForeignKey("permissions.id"), nullable=False, primary_key=True)

    def __repr__(self) -> str:
        return f"<RolePermission role_id={self.role_id}, permission_id={self.permission_id}>"
