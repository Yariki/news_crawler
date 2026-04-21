from tests.source.source_test_helper import create_source_payload


async def test_get_source_by_id(client):
    # Create a source
    payload = create_source_payload(
        name="source1",
        crawler_key="crawler1",
        scrape_interval_minutes=1,
        is_enabled=True,
    )
    create_response = await client.post("/sources", json=payload)
    assert create_response.status_code == 201
    created_source = create_response.json()

    # Get the source by ID
    source_id = created_source["id"]
    get_response = await client.get(f"/sources/{source_id}")
    assert get_response.status_code == 200
    retrieved_source = get_response.json()

    # Verify the retrieved source matches the created source
    assert retrieved_source["id"] == created_source["id"]
    assert retrieved_source["name"] == created_source["name"]
    assert retrieved_source["source_type"] == created_source["source_type"]
