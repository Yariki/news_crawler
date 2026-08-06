from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.rbac import RequiredPermissions, AuthorizationContext, get_authorization_context


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/single",
             dependencies=[
                 Depends(RequiredPermissions(
                     "post:read:any"))
             ])
    async def get() -> dict[str, Any]:
        return {'ok': True}
    
    
    @app.get("/all",
                 dependencies=[
                     Depends(RequiredPermissions(
                         "post:read:any", "post:update:any", mode="all"))
                 ])
    async def all_permissions_update() -> dict[str, Any]:
        return {'ok': True}

    @app.get("/any",
                 dependencies=[
                     Depends(RequiredPermissions(
                         "post:update:any", "post:update:own", mode="any"))
                 ])
    async def any_permissions_endpoint() -> dict[str, Any]:
        return {'ok': True}

    return app


@pytest.fixture
def client (app: FastAPI) -> AsyncIterator[TestClient]:
    with TestClient(app) as client:
        yield client

def set_authorization_context(app: FastAPI, context: AuthorizationContext ) -> None:
    async def override_context() -> AuthorizationContext:
        return context

    app.dependency_overrides[get_authorization_context] = override_context
