from tests.conftest import set_authorization_context


async def test_create_keyword_admin(client, db_session):
    
    await set_authorization_context(
            db_session,
            "keyword:create:own",
            user_name="admin",
        )
    
    response = await client.post("/keywords", json={"keyword": "test"})
    assert response.status_code == 201
    data = response.json()
    assert data["keyword"] == "test"
    assert data["is_enabled"] is True

async def test_create_keyword_user(client, db_session):
    
    await set_authorization_context(
            db_session,
            "keyword:create:own",
            user_name="admin",
            role='user'
        )
    
    response = await client.post("/keywords", json={"keyword": "test"})
    assert response.status_code == 201
    data = response.json()
    assert data["keyword"] == "test"
    assert data["is_enabled"] is True

async def test_create_keyword_same(client, db_session):

    
    await set_authorization_context(
            db_session,
            "keyword:create:own",
            user_name="admin",
        )

    response = await client.post("/keywords", json={"keyword": "test"})
    assert response.status_code == 201
    data = response.json()
    assert data["keyword"] == "test"
    assert data["is_enabled"] is True

    response2 = await client.post("/keywords", json={"keyword": "test"})
    assert response2.status_code == 201
    data2 = response2.json()
    assert data2["keyword"] == data["keyword"]
    assert data2["is_enabled"] is True
    assert data2["id"] == data["id"]

async def test_create_keyword_empty(client, db_session):
    
    await set_authorization_context(
                db_session,
                "keyword:create:own",
                user_name="admin",
            )
    
    response = await client.post("/keywords", json={"keyword": ""})
    assert response.status_code == 422
    response_data = response.json()
    assert response_data["detail"][0]["loc"] == ["body", "keyword"] 
    

async def test_create_keyword_whitespace(client, db_session):
    await set_authorization_context(
                db_session,
                "keyword:create:own",
                user_name="admin",
            )
    response = await client.post("/keywords", json={"keyword": "  "})
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Keyword cannot be empty"
