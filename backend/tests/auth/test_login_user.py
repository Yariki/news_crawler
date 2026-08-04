
from fastapi import status as HttpStatus

from app.core.security import decode_token
from app.core.config import settings
from app.models import IssuedRefreshToken


async def test_login_user(client, db_session):
    
    # Arrange
    user_create = {
        "email": "test@test.com",
        "password": "Password123!",
        "username": "testuser",
        "is_active": True
    }   
    response = await client.post("/auth/register", json=user_create)
    assert response.status_code == HttpStatus.HTTP_201_CREATED
    
    login_request = {
        "email": "test@test.com",
        "password": "Password123!"
    }
    
    # Act
    login_response = await client.post("/auth/login", json=login_request)
    
    # Assert
    assert login_response.status_code == HttpStatus.HTTP_200_OK
    token_pair = login_response.json()
    assert token_pair['access_token'] is not None
    assert token_pair['refresh_token'] is not None
    assert token_pair['token_type'] == 'Bearer'
    
    claims = decode_token(token_pair['refresh_token'], settings)
    
    jti = claims.get("jti")
    issuer_refresh_token = await db_session.get(IssuedRefreshToken, jti)
    assert issuer_refresh_token is not None


async def test_login_email_is_empty(client):
    # Arrange
    login_request = {
        "email": "",
        "password": "Password123!"
    }
    
    # Act
    login_response = await client.post("/auth/login", json=login_request)
    
    # Assert
    assert login_response.status_code == HttpStatus.HTTP_422_UNPROCESSABLE_ENTITY
    
    
async def test_login_password_is_empty(client):
    # Arrange
    login_request = {
        "email": "test@TEST.com",
        "password": ""
    }
    
    # Act
    
    response = await client.post("/auth/login", json=login_request)
    
    # Assert
    assert response.status_code == HttpStatus.HTTP_422_UNPROCESSABLE_ENTITY
    
    
async def test_login_weak_password(client):
    # Arrange
    login_request = {
        "email": "test@TEST.com",
        "password": "weak"
    }
    
    # Act
    
    response = await client.post("/auth/login", json=login_request)
    
    # Assert
    assert response.status_code == HttpStatus.HTTP_422_UNPROCESSABLE_ENTITY
