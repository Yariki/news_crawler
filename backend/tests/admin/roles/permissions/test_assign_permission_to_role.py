from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import selectinload

from app.models.role import Role
from tests.conftest import client, set_authorization_context

async def test_get_permissions_success(client, create_role, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role = create_role(name="supervisor")
    role2 = create_role(name="user2")
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    response2 = await client.post("/admin/roles", json=role2.model_dump(mode='json'))
    role_id= response.json()["id"]
    role2_id = response2.json()["id"]
    permission = {
        "resource": "source",
        "action": "read",
        "scope": "own"
    }
    response_perm = await client.post(f"/admin/roles/{role_id}/permissions", json=permission)
    assert response_perm.status_code == 201
    perm_id = response_perm.json()["id"]
    permission = {
        "resource": "source",
        "action": "create",
        "scope": "own"
    }
    response_perm2 = await client.post(f"/admin/roles/{role_id}/permissions", json=permission)
    assert response_perm2.status_code == 201
    perm2_id = response_perm2.json()["id"]
    
    # Act
    request = {
        "permission_id": perm2_id
    }
    
    resp = await client.post(f"/admin/roles/{role2_id}/permissions/assign", json=request)

    # Assert
    assert resp.status_code == 201
    
    role = (await db_session.execute(
        select(Role).where(Role.id == role2_id).options(selectinload(Role.permissions))
    )).scalar_one_or_none()
    data = resp.json()
    assert data["id"] == perm2_id
    assert any(str(perm.id) == str(perm2_id) for perm in role.permissions)
    