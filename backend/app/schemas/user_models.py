import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from pydantic.v1 import EmailStr, ValidationError


class UserCreate(BaseModel):
    email: EmailStr = Field(min_length=1, max_length=255)
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    is_active: bool = Field(default=True)

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> None:
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValidationError("Password must contain at least one digit")
        if not re.search(r"[^\w\s]", password):
            raise ValidationError("Password must contain at least one special character")

class UserUpdate(BaseModel):
    email: EmailStr = Field(min_length=1, max_length=255)
    username: str = Field(min_length=1, max_length=255)
    is_active: bool = Field(default=True)

class UserRead(UserCreate):
    id: UUID
    email: EmailStr
    username: str
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None

class UserChangePassword(BaseModel):
    old_password: str = Field(min_length=8, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)

    @field_validator("new_password")
    @field_validator("old_password")
    @classmethod
    def validate_password(cls, password: str) -> None:
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValidationError("Password must contain at least one digit")
        if not re.search(r"[^\w\s]", password):
            raise ValidationError("Password must contain at least one special character")

