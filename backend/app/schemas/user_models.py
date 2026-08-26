import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.validation import validate_password

class UserBase(BaseModel):
    email: EmailStr = Field(min_length=1, max_length=255)
    username: str = Field(min_length=1, max_length=255)
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        validate_password(password)
        return password

class UserUpdate(BaseModel):
    email: EmailStr = Field(min_length=1, max_length=255)
    username: str = Field(min_length=1, max_length=255)
    is_active: bool = Field(default=True)

class UserRead(UserBase):
    id: UUID
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            email=obj.email,
            username=obj.username,
            is_active=obj.is_active,
            is_verified=obj.is_verified,
            last_login_at=obj.last_login_at,
            created_at=obj.created_at
        )

class UserChangePassword(BaseModel):
    old_password: str = Field(min_length=8, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)

    @field_validator("old_password", "new_password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[^\w\s]", password):
            raise ValueError("Password must contain at least one special character")
        return password


class UserRoles(BaseModel):
    roles_ids: list[UUID] = Field(default_factory=list)
    
class AdminChangePassword(BaseModel):
    new_password: str = Field(min_length=8, max_length=255)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[^\w\s]", password):
            raise ValueError("Password must contain at least one special character")
        return password
    
    
