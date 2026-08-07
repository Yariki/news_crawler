import uuid

from fastapi import FastAPI, status as HttpStatus
from starlette.testclient import TestClient

from app.core.rbac import AuthorizationContext
from tests.rbac.conftest import set_rbac_authorization_context


def test_missing_permissions_403(app: FastAPI, client: TestClient):

    set_rbac_authorization_context(app,
                              AuthorizationContext(
                                user_id=uuid.uuid4(),
                                roles=frozenset({'users'}),
                                permissions=frozenset({'users:read:any'}),
                              )
    )

    response = client.get(f"/single/{uuid.uuid4()}")
    assert response.status_code == HttpStatus.HTTP_403_FORBIDDEN


def test_user_with_permissions_is_allowed(app: FastAPI, client: TestClient):
    
    id = uuid.uuid4()
    set_rbac_authorization_context(app,
                              AuthorizationContext(
                                  user_id=id,
                                  roles=frozenset({'users'}),
                                  permissions=frozenset({'post:read:any'}),
                              )
                              )

    response = client.get(f"/single/{uuid.uuid4()}")
    assert response.status_code == HttpStatus.HTTP_200_OK
    
def test_user_with_all_permissions_is_allowed(app: FastAPI, client: TestClient):
    set_rbac_authorization_context(app,
                              AuthorizationContext(
                                  user_id=uuid.uuid4(),
                                  roles=frozenset({'users'}),
                                  permissions=frozenset({'post:read:any', 'post:update:any'}),
                              )
                              )

    response = client.get("/all")
    assert response.status_code == HttpStatus.HTTP_200_OK
    
def test_user_all_permissions_is_failed(app: FastAPI, client: TestClient):
    set_rbac_authorization_context(app,
                              AuthorizationContext(
                                  user_id=uuid.uuid4(),
                                  roles=frozenset({'users'}),
                                  permissions=frozenset({'post:read:any'}),
                              )
                              )

    response = client.get("/all")
    assert response.status_code == HttpStatus.HTTP_403_FORBIDDEN
    

def test_user_any_mode_with_one_permission_is_allowed(app: FastAPI, client: TestClient):
    set_rbac_authorization_context(app,
                              AuthorizationContext(
                                  user_id=uuid.uuid4(),
                                  roles=frozenset({'users'}),
                                  permissions=frozenset({'post:update:own'}),
                              )
                              )

    response = client.get("/any")
    assert response.status_code == HttpStatus.HTTP_200_OK
    
def test_user_any_mode_with_no_permissions_is_forbidden(app: FastAPI, client: TestClient):
    set_rbac_authorization_context(app,
                              AuthorizationContext(
                                  user_id=uuid.uuid4(),
                                  roles=frozenset({'users'}),
                                  permissions=frozenset({"users:read:any"}),
                              )
                              )

    response = client.get("/any")
    assert response.status_code == HttpStatus.HTTP_403_FORBIDDEN
    
def test_mode_all_wildcard_permissions_are_allowed(app: FastAPI, client: TestClient):
    set_rbac_authorization_context(app,
                              AuthorizationContext(
                                  user_id=uuid.uuid4(),
                                  roles=frozenset({'users'}),
                                  permissions=frozenset({'post:*:any'}),
                              )
                              )

    response = client.get("/all")
    assert response.status_code == HttpStatus.HTTP_200_OK    
    
def test_auth_context_wildcard_permissions_are_allowed(app: FastAPI, client: TestClient):
    context = AuthorizationContext(
                                  user_id=uuid.uuid4(),
                                  roles=frozenset({'users'}),
                                  permissions=frozenset({'post:*:*'}),
                              )

    assert context.has_permission('post:read:any')
    assert context.has_permission('post:update:own')
    assert context.has_permission('post:delete:any')