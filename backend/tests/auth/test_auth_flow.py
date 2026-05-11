async def test_login_refresh_logout_flow(client):
    login = await client.post(
        "/auth/login",
        json={"email": "admin@news-crawler.local", "password": "ChangeMe123!"},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"

    refresh = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 200
    refreshed_tokens = refresh.json()
    assert refreshed_tokens["refresh_token"] != tokens["refresh_token"]

    logout = await client.post("/auth/logout", json={"refresh_token": refreshed_tokens["refresh_token"]})
    assert logout.status_code == 204


async def test_login_rejects_invalid_credentials(client):
    response = await client.post("/auth/login", json={"email": "admin@news-crawler.local", "password": "bad-pass-123"})
    assert response.status_code == 401
