

async def test_get_keywords(client):

    response1 = await client.post("/keywords", json={"keyword": "test"})
    response2 = await client.post("/keywords", json={"keyword": "test2"})

    assert response1.status_code == 201 
    assert response2.status_code == 201

    response = await client.get("/keywords")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


async def test_get_active_keywords(client):

    response1 = await client.post("/keywords", json={"keyword": "test"})
    response2 = await client.post("/keywords", json={"keyword": "test2"})

    assert response1.status_code == 201 
    assert response2.status_code == 201

    response = await client.get("/keywords/active")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

async def test_get_keywords_empty(client):

    response = await client.get("/keywords")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


async def test_get_keyword_by_id(client):

    response1 = await client.post("/keywords", json={"keyword": "test"})
    assert response1.status_code == 201 
    data1 = response1.json()
    keyword_id = data1["id"]

    response = await client.get(f"/keywords/{keyword_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == keyword_id
    assert data["keyword"] == "test"

