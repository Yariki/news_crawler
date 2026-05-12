from tests.source.source_test_helper import create_source_payload


async def test_update_source(client):
    create_payload = create_source_payload(
        name="Source Before",
        crawler_key="crawler1",
        scrape_interval_minutes=10,
        is_enabled=True,
    )
    create_response = await client.post("/sources", json=create_payload)
    assert create_response.status_code == 201
    source_id = create_response.json()["id"]

    update_payload = create_source_payload(
        name="Source After",
        crawler_key="crawler2",
        scrape_interval_minutes=20,
        is_enabled=False,
    )
    update_response = await client.put(f"/sources/{source_id}", json=update_payload)
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Source After"
    assert data["crawler_key"] == "crawler2"
    assert data["scrape_interval_minutes"] == 20
    assert data["is_enabled"] is False


async def test_delete_source(client):
    create_payload = create_source_payload(
        name="Source For Delete",
        crawler_key="crawler-delete",
        scrape_interval_minutes=10,
        is_enabled=True,
    )
    create_response = await client.post("/sources", json=create_payload)
    assert create_response.status_code == 201
    source_id = create_response.json()["id"]

    delete_response = await client.delete(f"/sources/{source_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/sources/{source_id}")
    assert get_response.status_code == 404

