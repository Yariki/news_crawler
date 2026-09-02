from tests.conftest import client, set_authorization_context

async def test_get_permissions_success(client, create_role, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role = create_role(name="supervisor")
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    role_id= response.json()["id"]
    permission = {
        "resource": "source",
        "action": "read",
        "scope": "own"
    }
    response_perm = await client.post(f"/admin/roles/{role_id}/permissions", json=permission)
    assert response_perm.status_code == 201
    permission = {
        "resource": "source",
        "action": "create",
        "scope": "own"
    }
    response_perm = await client.post(f"/admin/roles/{role_id}/permissions", json=permission)
    assert response_perm.status_code == 201
    
    
    # Act
    
    resp = await client.get('/admin/permissions');
    

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert  len(data) == 2
    