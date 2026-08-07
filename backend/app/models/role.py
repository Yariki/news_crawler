
from sqlalchemy import Boolean, DateTime, String
from datetime import datetime
from app.db.base import ChangeTrackingMixin, PrimaryIdMixin
from sqlalchemy.orm import Mapped, mapped_column



class Role(ChangeTrackingMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
