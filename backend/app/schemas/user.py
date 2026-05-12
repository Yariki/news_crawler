from __future__ import annotations

from pydantic import BaseModel


class UserCreateRequest(BaseModel):
    email: str
    password: str
    role: str
    team_id: str | None = None


class UserReadResponse(BaseModel):
    id: str
    email: str
    role: str
    team_id: str | None
    is_active: bool
    force_password_change: bool
