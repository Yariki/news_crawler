import datetime
from enum import IntEnum
from uuid import UUID


from sqlalchemy import String, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IssuedRefreshTokenStatus(IntEnum):
    ACTIVE = 1
    ROTATED = 2
    REVOKED = 3


class IssuedRefreshToken(Base):

    __tablename__ = "issued_refresh_token"

    jti: Mapped[str] = mapped_column(String(64),unique=True, nullable=False, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    status: Mapped[int]= mapped_column(Integer,nullable=False, default=IssuedRefreshTokenStatus.ACTIVE.value)

    issued_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    terminal_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_jti: Mapped[str] = mapped_column(String(64),nullable=True)