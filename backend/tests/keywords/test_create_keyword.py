async def test_create_keyword(client):
    response = await client.post("/keywords", json={"keyword": "test"})
    assert response.status_code == 201
    data = response.json()
    assert data["keyword"] == "test"
    assert data["is_enabled"] is True


async def test_create_keyword_same(client):

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
