from tests.conftest import set_authorization_context



async def test_get_users_success(client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    user = create_user()
    user2 = create_user()
    response = await client.post("/admin/users", json=user.model_dump(mode='json'))
    response2 = await client.post("/admin/users", json=user2.model_dump(mode='json'))
    assert response.status_code == 201
    assert response2.status_code == 201
    # Act
    response = await client.get("/admin/users")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

async def test_get_users_forbidden(client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
        role="user"
    )
    # Act
    response = await client.get("/admin/users") 
    
    # Assert
    assert response.status_code == 403

