from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, UUID4


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserRead(BaseModel):
    id: UUID4
    email: str
    is_active: bool
    roles: list[str]
    permissions: list[str]


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=256)
    is_active: bool = True
    role_ids: list[UUID4] = Field(default_factory=list)


class UserUpdate(BaseModel):
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=256)


class RoleRead(BaseModel):
    id: UUID4
    name: str
    permissions: list[str]


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    permissions: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    permissions: list[str] | None = None


class UserRoleAssignRequest(BaseModel):
    role_id: UUID4


class AuthEventRead(BaseModel):
    action: str
    details: dict | None
    created_at: datetime
