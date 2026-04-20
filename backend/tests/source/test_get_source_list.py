from tests.source.source_test_helper import create_source_payload


async def test_create_source(client):

    source1 = create_source_payload(
        name="source1",
        crawler_key="crawler1",
        scrape_interval_minutes=1,
        is_enabled=True,
    )
    response = await client.post("/sources", json=source1)
    assert response.status_code == 200

    source2 = create_source_payload(
        name="source1",
        crawler_key="crawler2",
        scrape_interval_minutes=1,
        is_enabled=True,
    )
    response = await client.post("/sources", json=source2)
    assert response.status_code == 200

    response = await client.get("/sources")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
