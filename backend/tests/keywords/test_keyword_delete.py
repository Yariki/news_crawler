import uuid


async def test_delete_keyword(client):
    create_response = await client.post("/keywords", json={"keyword": "for-delete"})
    assert create_response.status_code == 201
    keyword_id = create_response.json()["id"]

    delete_response = await client.delete(f"/keywords/{keyword_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/keywords/{keyword_id}")
    assert get_response.status_code == 404


async def test_delete_keyword_not_found(client):
    response = await client.delete(f"/keywords/{uuid.uuid4()}")
    assert response.status_code == 404

