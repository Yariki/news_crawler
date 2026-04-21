from tests.source.source_test_helper import create_source_payload


async def test_create_source(client):

    payload = create_source_payload(
        name="Test Source",
        crawler_key="test_crawler_key",
        scrape_interval_minutes=1,
        is_enabled=True,
    )

    response = await client.post("/sources", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["base_url"] == payload["base_url"]
    assert data["language"] == payload["language"]
    assert data["source_type"] == payload["source_type"]
    assert data["crawler_key"] == payload["crawler_key"]
    assert data["scrape_interval_minutes"] == payload["scrape_interval_minutes"]
    assert data["is_enabled"] == payload["is_enabled"]
