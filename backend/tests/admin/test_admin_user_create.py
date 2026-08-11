from tests.conftest import set_authorization_context

async def test_create_user_success(client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    user = create_user()

    # Act

    response = await client.post("/admin/users", json=user.model_dump(mode='json'))

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user.username

async def test_create_user_forbidden(client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
        role="user"
    )
    # Arrange
    user = create_user()

    # Act

    response = await client.post("/admin/users", json=user.model_dump(mode='json'))

    # Assert
    assert response.status_code == 403
    
async def test_create_user_same_email_failed(client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    user = create_user()

    # Act

    response1 = await client.post("/admin/users", json=user.model_dump(mode='json'))
    response2 = await client.post("/admin/users", json=user.model_dump(mode='json'))

    # Assert
    assert response1.status_code == 201
    assert response2.status_code == 400
    
async def test_create_user_invalid_email_failed(client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    user = {
        'email': 'invalid-email',
        'username': 'testuser',
        'password': 'TestPassword123!',
        'is_active': True
    }

    # Act

    response = await client.post("/admin/users", json=user)

    # Assert
    assert response.status_code == 422


async def test_create_user_same_username_failed(faker, client, create_user, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    user = create_user()
    user2 = create_user(email=faker.email(), username=user.username)
    
    # Act
    response1 = await client.post("/admin/users", json=user.model_dump(mode='json'))
    response2 = await client.post("/admin/users", json=user2.model_dump(mode='json'))

    # Assert
    assert response1.status_code == 201
    assert response2.status_code == 400
