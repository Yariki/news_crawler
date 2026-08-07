import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Literal, Annotated
from uuid import UUID

from sqlalchemy import select
from fastapi import Request, Depends, HTTPException, status as HttpStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentActiveUser, CurrentUser
from app.db.session import DbSession
from app.models import Role, Permission, UserRole, RolePermission
from app.models.owned_resource_type import OwnedResourceType
from app.services.ownership_resolver.service import is_user_owner_of_resource

ALL_PERMISSIONS: Final = '*'

AUTHORIZATION_CONTEXT_KEY: Final = "authorization_context"

OWNED_RESOURCE_PATH_PARAM_KEY: Final = "resouce_id"

class PermissionMode(StrEnum):
    ALL = "all"
    ANY = "any"

class ScopeMode(StrEnum):
    ANY = "any"
    OWN = "own"

PERMISSION_NAME_PATTERN = re.compile(
    r"^[a-z][a-z0-9_-]*:[a-z][a-z0-9_-]*:[a-z][a-z0-9_-]*$"
)

def permission_matches(*, granted: str, required: str) -> bool:

    if granted == ALL_PERMISSIONS:
        return True

    if granted ==  required:
        return True

    grant_parts = granted.split(':')
    requeired_parts = required.split(':')

    if len(grant_parts) != len(requeired_parts):
        return False

    return all(
        grant == ALL_PERMISSIONS or grant == required
        for grant, required in zip(
            grant_parts,
            requeired_parts,
            strict=True
        )
    )

@dataclass(frozen=True, slots=True)
class AuthorizationContext:
    user_id: UUID
    roles: frozenset[str]
    permissions: frozenset[str]


    def has_role(self, role: str) -> bool:

        return role in self.roles

    def has_permission(self, permission: str) -> bool:

        return any(
            permission_matches(granted=perm, required=permission)
            for perm in self.permissions
        )


async def load_authorization_context(*, db: AsyncSession, user_id: UUID) -> AuthorizationContext:

    query = (
        select(Role.name,
               Permission.name)
        .select_from(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .outerjoin(RolePermission, RolePermission.role_id == Role.id)
        .outerjoin(Permission, Permission.id == RolePermission.permission_id)
        .where(UserRole.user_id == user_id)
    )

    result = await db.execute(query)
    rows = result.all()

    roles = [row[0] for row in rows if row[0] is not None]
    permissions = [row[1] for row in rows if row[1] is not None]

    return AuthorizationContext(
        user_id=user_id,
        roles=frozenset(roles),
        permissions=frozenset(permissions)
    )

async def get_authorization_context(*, request: Request,  db: DbSession, current_user: CurrentUser) -> AuthorizationContext:

    cached_context: AuthorizationContext | None = getattr(request.state, AUTHORIZATION_CONTEXT_KEY, None)

    if cached_context is not None and cached_context.user_id == current_user.id:
        return cached_context


    auth_context = await load_authorization_context(db=db, user_id=current_user.id)

    setattr(request.state, AUTHORIZATION_CONTEXT_KEY, auth_context)

    return auth_context

@dataclass(frozen=True, slots=True)
class PermissionGranted:
    auth: AuthorizationContext
    is_any: bool
    
class RequiredPermissionsAndOwnership:
    """ """
    def __init__(self, *permissions: str, mode: PermissionMode = PermissionMode.ALL, resource_type: OwnedResourceType | None = None) -> None:

        if not permissions:
            raise ValueError("Permissions cannot be empty")

        if mode not in PermissionMode._value2member_map_:
            raise ValueError("Permissions mode must be 'all' or 'any'")

        unique_permissions = tuple(dict.fromkeys(permissions))

        invalid_permissions = [permission for permission in unique_permissions if not PERMISSION_NAME_PATTERN.fullmatch(permission)]

        if invalid_permissions:
            raise ValueError(f"Permissions contains invalid permissions: {', '.join(invalid_permissions)}")

        self.permissions = unique_permissions
        self.mode = mode
        self.resource_type = resource_type

    def _check_ownership(self, auth_context: AuthorizationContext,request:Request) -> bool:

        resource_id = request.path_params.get(OWNED_RESOURCE_PATH_PARAM_KEY)

        if resource_id is None:
            raise HTTPException(
                status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                detail="Resource ID is missing in the request path"
            )

        if not isinstance(resource_id, str):
            raise HTTPException(
                status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                detail="Resource ID must be a string"
            )

        try:
            resource_uuid = UUID(resource_id)
        except ValueError:
            raise HTTPException(
                status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                detail="Resource ID must be a valid UUID"
            )
        
        return is_user_owner_of_resource(user_id=auth_context.user_id, resource_type=self.resource_type, resource_id=resource_uuid)
    
    async def __call__(self, request: Request, auth_context: Annotated[AuthorizationContext, Depends(get_authorization_context)]) -> PermissionGranted:
        matched = [permission for permission in self.permissions if auth_context.has_permission(permission)]
        missing = [permission for permission in self.permissions if permission not in matched]
        
        
        if self.mode == PermissionMode.ALL:
            is_allowed = not missing
        else:
            is_allowed = len(matched) > 0

        if not is_allowed:
            raise HTTPException(
                status_code=HttpStatus.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing)}"
            )

        is_any = any(permission.endswith(":any") for permission in matched)
        
        if self.resource_type is None:
            return PermissionGranted(auth=auth_context, is_any=is_any)
        
        if not self._check_ownership(auth_context, request):
            raise HTTPException(
                status_code=HttpStatus.HTTP_403_FORBIDDEN,
                detail="User is not the owner of the resource"
            )
        
        return PermissionGranted(auth=auth_context, is_any=is_any)

class RequiredRoles:

    def __init__(self, *roles: str) -> None:

        if not roles:
            raise ValueError("Roles cannot be empty")

        normalized_roles = [role.strip().lower() for role in roles if role.strip()]

        if not normalized_roles:
            raise ValueError("Roles cannot be empty")

        self.roles = frozenset(normalized_roles)


    async def __call__(self, auth_context: Annotated[AuthorizationContext, Depends(get_authorization_context)]):

        any_role = any(auth_context.has_role(role) for role in self.roles)

        if any_role:
            return auth_context

        raise HTTPException(
            status_code=HttpStatus.HTTP_403_FORBIDDEN,
            detail=f"Missing required roles"
        )
