from fastapi import status as HttpStatus
from sqlalchemy import select

from app.models import Role, User, UserRole


async def test_access_token_succeeds_and_refresh_token_fails_on_protected_route(client, db_session):
    # Arrange
    user_create = {
        "email": "test@example.com",
        "password": "Password123!",
        "username": "testuser",
        "is_active": True
    }
    response = await client.post("/auth/register", json=user_create)
    assert response.status_code == HttpStatus.HTTP_201_CREATED

    # Grant the (migration-seeded) admin role directly in the DB so the protected
    # route's permission check is bypassed, isolating the test to token-type validation.
    user = (
        await db_session.execute(select(User).where(User.email == "test@example.com"))
    ).scalar_one()
    admin_role = (
        await db_session.execute(select(Role).where(Role.name == "admin"))
    ).scalar_one()
    db_session.add(UserRole(user_id=user.id, role_id=admin_role.id))
    await db_session.commit()

    login_request = {
        "username": "test@example.com",
        "password": "Password123!"
    }
    login_response = await client.post("/auth/login", data=login_request)
    assert login_response.status_code == HttpStatus.HTTP_200_OK
    token_pair = login_response.json()
    access_token = token_pair["access_token"]
    refresh_token = token_pair["refresh_token"]

    # Act & Assert - access token is accepted by a protected route
    access_response = await client.get(
        "/keywords/active", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert access_response.status_code == HttpStatus.HTTP_200_OK

    # Act & Assert - refresh token is rejected by the same protected route
    refresh_response = await client.get(
        "/keywords/active", headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert refresh_response.status_code == HttpStatus.HTTP_401_UNAUTHORIZED
