

from tests.conftest import set_authorization_context


async def test_get_source_by_id(db_session, client, create_source):
    
    await set_authorization_context(
        db_session,
        "source:read:own",
        "source:create:own",
        user_name="admin",
    )
    
    # Create a source
    payload = create_source(
        name="source1",
        crawler_key="crawler1",
        scrape_interval_minutes=1,
        is_enabled=True,
    )
    create_response = await client.post("/sources", json=payload.model_dump(mode='json'))
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
