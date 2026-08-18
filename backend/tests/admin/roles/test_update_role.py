from tests.conftest import set_authorization_context

async def test_update_role_success(client, create_role, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role = create_role(name="supervisor")
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    assert response.status_code == 201
    role_id = response.json()['id']

    role.name = "supervisor_2"

    # Act
    response = await client.put(f"/admin/roles/{role_id}", json=role.model_dump(mode="json"))

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == role.name
    
async def test_update_role_with_existing_name_failed(client, create_role, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )
    
    # Arrange
    role = create_role(name="supervisor")
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    assert response.status_code == 201
    role_id = response.json()['id']

    role.name = "user"
    
    # Act
    response = await client.put(f"/admin/roles/{role_id}", json=role.model_dump(mode="json"))

    # Assert
    assert response.status_code == 400



async def test_update_role_not_found(client, create_role, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )
    
    # Arrange
    role_id = '00000000-0000-0000-0000-000000000000'
    
    # Act
    response = await client.put(f"/admin/roles/{role_id}", json={"name": "non_existent_role"})

    # Assert
    assert response.status_code == 404
