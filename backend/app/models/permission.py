
from sqlalchemy import DateTime, String
from datetime import datetime
from app.db.base import ChangeTrackingMixin, PrimaryIdMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Permission(ChangeTrackingMixin):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Permission {self.name}>"

    roles: Mapped[list["Role"]] = relationship(
        secondary="role_permissions",
        back_populates="permissions",
    )
    