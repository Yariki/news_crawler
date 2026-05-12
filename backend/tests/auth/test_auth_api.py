from __future__ import annotations

from sqlalchemy import select

from app.core.rbac import Role
from app.models.team import Team
from app.models.user import User
from app.services.auth import hash_password


async def _create_user(db_session, *, email: str, password: str, role: Role = Role.ADMIN, force_password_change: bool = False):
    team = Team(name=f"{email}-team")
    db_session.add(team)
    await db_session.flush()
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role.value,
        team_id=team.id,
        force_password_change=force_password_change,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def test_login_and_refresh_rotation(client, db_session):
    await _create_user(db_session, email="admin@example.com", password="StrongPass1!")

    login = await client.post("/auth/login", json={"email": "admin@example.com", "password": "StrongPass1!"})
    assert login.status_code == 200
    login_data = login.json()
    assert login_data["access_token"]
    assert login_data["refresh_token"]
    assert login_data["expires_in"] == 3600

    refresh = await client.post("/auth/refresh", json={"refresh_token": login_data["refresh_token"]})
    assert refresh.status_code == 200
    refresh_data = refresh.json()
    assert refresh_data["access_token"] != login_data["access_token"]
    assert refresh_data["refresh_token"] != login_data["refresh_token"]

    refresh_again_old = await client.post("/auth/refresh", json={"refresh_token": login_data["refresh_token"]})
    assert refresh_again_old.status_code == 401


async def test_forced_change_password_and_reset_flow(client, db_session):
    await _create_user(
        db_session,
        email="member@example.com",
        password="StrongPass1!",
        role=Role.TEAM_MEMBER,
        force_password_change=True,
    )

    login = await client.post("/auth/login", json={"email": "member@example.com", "password": "StrongPass1!"})
    assert login.status_code == 200
    login_data = login.json()
    assert login_data["must_change_password"] is True

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {login_data['access_token']}"})
    assert me.status_code == 200
    assert me.json()["force_password_change"] is True

    forgot = await client.post("/auth/forgot-password", json={"email": "member@example.com"})
    assert forgot.status_code == 200
    token = forgot.json()["reset_token"]
    assert token

    reset = await client.post("/auth/reset-password", json={"token": token, "new_password": "ChangedPass2@"})
    assert reset.status_code == 200

    relogin = await client.post("/auth/login", json={"email": "member@example.com", "password": "ChangedPass2@"})
    assert relogin.status_code == 200
    assert relogin.json()["must_change_password"] is False

