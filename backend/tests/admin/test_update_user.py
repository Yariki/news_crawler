from tests.conftest import set_authorization_context



async def test_update_users_success(client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    user = create_user()
    response = await client.post("/admin/users", json=user.model_dump(mode='json'))
    assert response.status_code == 201
    
    user_id = response.json()["id"]
    
    user.email = "updated_email@example.com"
    user.username = "updated_username"
    
    # Act
    response = await client.put(f"/admin/users/{user_id}", json=user.model_dump(mode='json'))

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "updated_email@example.com"
    assert data["username"] == "updated_username"
    

async def test_update_users_not_found(client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    user = create_user()
    response = await client.post("/admin/users", json=user.model_dump(mode='json'))
    assert response.status_code == 201
    
    user.email = "updated_email@example.com"
    user.username = "updated_username"
    
    # Act
    response = await client.put(f"/admin/users/00000000-0000-0000-0000-000000000000", json=user.model_dump(mode='json'))

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"
    
async def test_update_users_invalid_email(client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    user = create_user()
    response = await client.post("/admin/users", json=user.model_dump(mode='json'))
    assert response.status_code == 201
    
    user_id = response.json()["id"]
    
    user.email = "invalid_email"
    user.username = "updated_username"
    
    # Act
    response = await client.put(f"/admin/users/{user_id}", json=user.model_dump(mode='json'))

    # Assert
    assert response.status_code == 422
    
    
    
async def test_update_users_invalid_username(client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    user = create_user()
    response = await client.post("/admin/users", json=user.model_dump(mode='json'))
    assert response.status_code == 201
    
    user_id = response.json()["id"]
    
    user.username = ""
    
    # Act
    response = await client.put(f"/admin/users/{user_id}", json=user.model_dump(mode='json'))

    # Assert
    assert response.status_code == 422    
    
