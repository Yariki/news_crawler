
from fastapi import status as HttpStatus

from app.core.security import decode_token
from app.core.config import settings
from app.models import IssuedRefreshToken, IssuedRefreshTokenStatus


async def test_refresh_token_success(client, db_session):
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
    refresh_response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})

    # Assert
    assert refresh_response.status_code == HttpStatus.HTTP_200_OK
    new_token_pair = refresh_response.json()
    assert 'access_token' in new_token_pair
    assert 'refresh_token' in new_token_pair
    
    claims_old = decode_token(refresh_token, settings)
    jti = claims_old.get("jti")
    
    claims_new = decode_token(new_token_pair['refresh_token'], settings)
    new_jti = claims_new.get("jti")
    
    old_issued_refresh_token = await db_session.get(IssuedRefreshToken, jti)
    new_issued_refresh_token = await db_session.get(IssuedRefreshToken, new_jti)

    assert old_issued_refresh_token is not None
    assert old_issued_refresh_token.status == IssuedRefreshTokenStatus.ROTATED.value
    assert new_issued_refresh_token is not None
    assert new_issued_refresh_token.status == IssuedRefreshTokenStatus.ACTIVE.value
    
    
async def test_refresh_token_reuse(client, db_session):
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
    refresh_response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})

    # Assert
    assert refresh_response.status_code == HttpStatus.HTTP_200_OK
    new_token_pair = refresh_response.json()
    assert 'access_token' in new_token_pair
    assert 'refresh_token' in new_token_pair

    # Attempt to reuse the old refresh token
    reuse_response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_response.status_code == HttpStatus.HTTP_401_UNAUTHORIZED
    
async def test_refresh_token_invalid_wrong_type(client, db_session):
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
    refresh_token = token_pair['refresh_token']
    
    # Act
    refresh_response = await client.post("/auth/refresh", json={"refresh_token": access_token})

    # Assert
    assert refresh_response.status_code == HttpStatus.HTTP_401_UNAUTHORIZED

    
async def test_refresh_token_invalid(client, db_session):
    # Attempt to use an invalid refresh token
    reuse_response = await client.post("/auth/refresh", json={"refresh_token": "invalid_token"})
    assert reuse_response.status_code == HttpStatus.HTTP_401_UNAUTHORIZED
    
    
    