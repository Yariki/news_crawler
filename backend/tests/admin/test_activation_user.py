from tests.conftest import set_authorization_context



async def test_activate_user_success(client, create_user, db_session):
    
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
    
    # Act
    response = await client.post(f"/admin/users/{user_id}/activate", json=user.model_dump(mode='json'))

    # Assert
    assert response.status_code == 201
    data = response.json()
    
    assert data['is_active'] == True
    
    
async def test_deactivate_user_success(client, create_user, db_session):
    
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
    
    # Act
    response = await client.post(f"/admin/users/{user_id}/deactivate", json=user.model_dump(mode='json'))

    # Assert
    assert response.status_code == 201
    data = response.json()
    
    assert data['is_active'] == False