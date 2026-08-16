from tests.conftest import set_authorization_context

async def test_create_role_success(client, create_role, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role = create_role(name="supervisor")

    # Act

    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == role.name
    
async def test_create_role_failure_duplicate_name(client, create_role, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role = create_role(name="supervisor")

    # Act

    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    assert response.status_code == 201
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == f"Role with name '{role.name}' already exists."
    