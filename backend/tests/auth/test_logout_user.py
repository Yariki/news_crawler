
from fastapi import status as HttpStatus

from app.api.auth.api import refresh_token
from app.core.security import decode_token
from app.core.config import settings
from app.models import IssuedRefreshToken
from app.models import IssuedRefreshTokenStatus


async def test_logout_user(client, db_session):
    # Arrange
    user_create = {
        "email": "test@example.com",
        "password": "Password123!",
        "username": "testuser",
        "is_active": True
    }
    response = await client.post("/auth/register", json=user_create)
    assert response.status_code == HttpStatus.HTTP_201_CREATED
    
    login_request = {
        "email": "test@example.com",
        "password": "Password123!"
    }
    login_response = await client.post("/auth/login", json=login_request)
    assert login_response.status_code == HttpStatus.HTTP_200_OK
    token_pair = login_response.json()
    
    refresh_token = token_pair['refresh_token']
    
    # Act
    logout_request = {
        "refresh_token": refresh_token
    }
    logout_response = await client.post("/auth/logout", json=logout_request)
    
    # Assert
    assert logout_response.status_code == HttpStatus.HTTP_200_OK
    claims = decode_token(refresh_token, settings)
    jti = claims.get("jti")
    issuer_refresh_token = await db_session.get(IssuedRefreshToken, jti)
    assert issuer_refresh_token is not None
    
    assert issuer_refresh_token.status == IssuedRefreshTokenStatus.REVOKED.value
    

async  def test_logout_user_token_reused(client, db_session):
    # Arrange
    user_create = {
        "email": "test@example.com",
        "password": "Password123!",
        "username": "testuser",
        "is_active": True
    }
    response = await client.post("/auth/register", json=user_create)
    assert response.status_code == HttpStatus.HTTP_201_CREATED
    
    login_request = {
        "email": "test@example.com",
        "password": "Password123!"
    }
    login_response = await client.post("/auth/login", json=login_request)
    assert login_response.status_code == HttpStatus.HTTP_200_OK
    token_pair = login_response.json()
    refresh_token = token_pair['refresh_token']
    
    # Act
    logout_request = {
        "refresh_token": refresh_token
    }
    logout_response = await client.post("/auth/logout", json=logout_request)        
    assert logout_response.status_code == HttpStatus.HTTP_200_OK
    
    logout_response = await client.post("/auth/logout", json=logout_request)        
    
    # Assert
    assert logout_response.status_code == HttpStatus.HTTP_400_BAD_REQUEST

async  def test_logout_user_token_wrong_type(client, db_session):
    # Arrange
    user_create = {
        "email": "test@example.com",
        "password": "Password123!",
        "username": "testuser",
        "is_active": True
    }
    response = await client.post("/auth/register", json=user_create)
    assert response.status_code == HttpStatus.HTTP_201_CREATED
    
    login_request = {
        "email": "test@example.com",
        "password": "Password123!"
    }
    login_response = await client.post("/auth/login", json=login_request)
    assert login_response.status_code == HttpStatus.HTTP_200_OK
    token_pair = login_response.json()
    access_token = token_pair['access_token']
    
    # Act
    logout_request = {
        "refresh_token": access_token
    }
    logout_response = await client.post("/auth/logout", json=logout_request)        
    
    # Assert
    
    assert logout_response.status_code == HttpStatus.HTTP_401_UNAUTHORIZED
    
    


async def test_logout_user_invalid_token(client):
    # Arrange
    invalid_refresh_token = "invalid_token"
    
    # Act
    logout_request = {
        "refresh_token": invalid_refresh_token
    }
    logout_response = await client.post("/auth/logout", json=logout_request)        
    
    # Assert
    assert logout_response.status_code == HttpStatus.HTTP_401_UNAUTHORIZED