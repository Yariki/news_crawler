from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid import uuid4, UUID


class Base(DeclarativeBase):
    pass

class PrimaryIdMixin(Base):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4,
        server_default=text("gen_random_uuid()")
    )

class ChangeTrackingMixin(Base):
    __abstract__ = True
    created_at: Mapped[str] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        server_default=text("now()"), onupdate=text("now()"), nullable=False
    ) 
    
    is_delete: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )   