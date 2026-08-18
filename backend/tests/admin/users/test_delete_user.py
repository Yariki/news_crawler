from tests.conftest import set_authorization_context



async def test_delete_users_success(client, create_user, db_session):
    
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
    response = await client.delete(f"/admin/users/{user_id}")
    
    # Assert
    assert response.status_code == 204


async def test_delete_users_not_found(client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )
    
    # Act
    response = await client.delete(f"/admin/users/00000000-0000-0000-0000-000000000000")
    
    # Assert
    assert response.status_code == 404