from sqlalchemy import DateTime, ForeignKey, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid import uuid4, UUID
from datetime import datetime

class Base(DeclarativeBase):
    pass

class PrimaryIdMixin(Base):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4,
        server_default=text("gen_random_uuid()")
    )

class ChangeTrackingMixin(PrimaryIdMixin):
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
        server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    ) 
    
    is_delete: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )

class OwnerMixin(PrimaryIdMixin):
    __abstract__ = True
    
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)