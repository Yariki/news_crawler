from types import SimpleNamespace
from typing import Any, Iterator
from uuid import UUID
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_current_active_user, get_current_user
from app.core.rbac import RequiredPermissionsAndOwnership, AuthorizationContext, get_authorization_context, PermissionMode, PermissionGranted


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/single/{resource_id}")
    async def get(resource_id: UUID, perm_granted: PermissionGranted = Depends(RequiredPermissionsAndOwnership("post:read:any"))) -> dict[str, Any]:
        if perm_granted.is_any:
            return {'ok': True}
        return {'ok': False}
    
    @app.get("/all",
                 dependencies=[
                     Depends(RequiredPermissionsAndOwnership(
                         "post:read:any", "post:update:any", mode=PermissionMode.ALL))
                 ])
    async def all_permissions_update() -> dict[str, Any]:
        return {'ok': True}

    @app.get("/any",
                 dependencies=[
                     Depends(RequiredPermissionsAndOwnership(
                         "post:update:any", "post:update:own", mode=PermissionMode.ANY))
                 ])
    async def any_permissions_endpoint() -> dict[str, Any]:
        return {'ok': True}

    return app


@pytest.fixture
def client (app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client

def set_rbac_authorization_context(app: FastAPI, context: AuthorizationContext ) -> None:
    current_user = SimpleNamespace(id=context.user_id, is_active=True)

    async def override_current_user() -> Any:
        return current_user

    async def override_context() -> AuthorizationContext:
        return context

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_current_active_user] = override_current_user
    app.dependency_overrides[get_authorization_context] = override_context
