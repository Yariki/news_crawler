
from sqlalchemy import Boolean, DateTime, String
from app.db.base import ChangeTrackingMixin, PrimaryIdMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Role(ChangeTrackingMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Role {self.name}>"

    users: Mapped[list["User"]] = relationship(
        secondary="user_roles",
        back_populates="roles",
    )

    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permissions",
        back_populates="roles",
    )
