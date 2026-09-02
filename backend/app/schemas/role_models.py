import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

from app.models import Permission
from app.models.role import Role
from app.utils.validation import validate_actions, validate_resources, validate_scope


class RoleCreateUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    is_system: bool = Field(default=False)

class PermissionRead(BaseModel):
    id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    resource: str | None = Field(default=None, max_length=255)
    action: str | None = Field(default=None, max_length=255)
    scope: str | None = Field(default=None, max_length=255)
    created_at: datetime
    updated_at: datetime | None

    @classmethod
    def from_orm(cls, obj: Permission):
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            resource=obj.resource,
            action=obj.action,
            scope=obj.scope,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

class PermissionCreateUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=255)
    resource: str = Field(min_length=1, max_length=255)
    action: str = Field(min_length=1, max_length=255)
    scope: str = Field(min_length=1, max_length=255)

    @field_validator("resource")
    @classmethod
    def validate_resource(cls, resource: str) -> str:
        validate_resources(resource)
        return resource

    @field_validator("action")
    @classmethod
    def validate_action(cls, action: str) -> str:
        validate_actions(action)
        return action

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, scope: str) -> str:
        validate_scope(scope)
        return scope

class RoleDistribution(BaseModel):
    role_name: Optional[str]
    user_count: Optional[int]

class RoleRead(BaseModel):
    id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    is_system: bool = Field(default=True)
    created_at: datetime
    updated_at: datetime | None
    permissions: list[PermissionRead] = Field(default_factory=list)

    @classmethod
    def from_orm(cls, obj: Role):
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            is_system=obj.is_system,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            permissions=[PermissionRead.from_orm(permission) for permission in obj.permissions] if obj.permissions else []
        )

class AssignPermission(BaseModel):
    permission_id: UUID
