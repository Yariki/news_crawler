import uuid

async def test_update_keyword(client):
    response = await client.post("/keywords", json={"keyword": "test"})
    assert response.status_code == 201
    data = response.json()
    assert data["keyword"] == "test"
    assert data["is_enabled"] is True

    keyword_id = data["id"]
    
    update_response = await client.put(f"/keywords/{keyword_id}", json={"keyword": "updated", "is_enabled": False})
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["keyword"] == "updated"
    assert updated_data["is_enabled"] is False


async def test_update_keyword_not_found(client):
    non_existent_id = uuid.uuid4()
    update_response = await client.put(f"/keywords/{non_existent_id}", json={"keyword": "updated", "is_enabled": False})
    assert update_response.status_code == 404
    error_data = update_response.json()
    assert error_data["detail"] == "Keyword not found"    