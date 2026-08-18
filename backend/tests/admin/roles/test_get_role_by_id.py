from tests.conftest import set_authorization_context

async def test_get_rol_by_id_success(client, create_role, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role = create_role(name="supervisor")
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    assert response.status_code == 201
    
    role_id = response.json()["id"]
    
    # Act
    response2 = await client.get(f"/admin/roles/{role_id}")

    # Assert
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["id"] == role_id
    assert data2["name"] == "supervisor"

async def test_get_role_by_id_not_found(client, create_role, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    # Act
    response2 = await client.get(f"/admin/roles/{'00000000-0000-0000-0000-000000000000'}")

    # Assert
    assert response2.status_code == 404
