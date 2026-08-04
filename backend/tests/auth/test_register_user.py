from fastapi import status as HttpStatus


async def test_register_user(client, make_user_create):
    # Arrange
    user_create = await make_user_create("Password123!")

    # Act
    response = await client.post("/auth/register", json=user_create.model_dump(mode="json"))

    # Assert
    assert response.status_code == HttpStatus.HTTP_201_CREATED
    user_read = response.json()
    assert user_read["email"] == user_create.email

async def test_register_user_with_existing_email(client, make_user_create): 
    # Arrange
    user_create = await make_user_create("Password123!")
    await client.post("/auth/register", json=user_create.model_dump(mode="json"))

    # Act
    response = await client.post("/auth/register", json=user_create.model_dump(mode="json"))

    # Assert
    assert response.status_code == HttpStatus.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email is already in use"

async def test_register_user_with_existing_username(client, make_user_create):  
    # Arrange
    user_create = await make_user_create("Password123!")
    await client.post("/auth/register", json=user_create.model_dump(mode="json"))

    # Act
    user_create_with_same_username = await make_user_create("Password123!", username=user_create.username)
    response = await client.post("/auth/register", json=user_create_with_same_username.model_dump(mode="json"))

    # Assert
    assert response.status_code == HttpStatus.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Username is already in use"

async def test_register_user_with_invalid_email(client, make_user_create):
    # Arrange
    user_create = {
        "email": "tets-test.com",
        "password": "Password123!",
        "username": "testuser",
        "is_active": True
    }

    # Act
    response = await client.post("/auth/register", json=user_create)

    # Assert
    assert response.status_code == HttpStatus.HTTP_422_UNPROCESSABLE_ENTITY


async def test_register_user_with_weak_password(client, make_user_create):
    # Arrange
    user_create = {
        "email": "test@test.com",
        "password": "weak",
        "username": "testuser",
        "is_active": True
    }

    # Act
    response = await client.post("/auth/register", json=user_create)

    # Assert
    assert response.status_code == HttpStatus.HTTP_422_UNPROCESSABLE_ENTITY
    
async  def test_register_user_with_missing_email_field(client):
    # Arrange
    user_create = {
        "email": "",
        "password": "Password123!",
        "username": "testuser",
        "is_active": True
    }
    
    # Act
    response = await client.post("/auth/register", json=user_create)
    
        
    # Assert
    assert response.status_code == HttpStatus.HTTP_422_UNPROCESSABLE_ENTITY    


async  def test_register_user_with_missing_password_field(client):
    # Arrange
    user_create = {
        "email": "test@test.com",
        "password": "",
        "username": "testuser",
        "is_active": True
    }
    
    # Act
    response = await client.post("/auth/register", json=user_create)
    
        
    # Assert
    assert response.status_code == HttpStatus.HTTP_422_UNPROCESSABLE_ENTITY    

async  def test_register_user_with_missing_username_field(client):
    # Arrange
    user_create = {
        "email": "test@test.com",
        "password": "Password123!",
        "username": "",
        "is_active": True
    }
    
    # Act
    response = await client.post("/auth/register", json=user_create)
    
        
    # Assert
    assert response.status_code == HttpStatus.HTTP_422_UNPROCESSABLE_ENTITY