
from tests.conftest import set_authorization_context

async def test_get_source_list(db_session, client, create_source):

    await set_authorization_context(
        db_session,
        "source:read:own",
        "source:create:own",
        user_name="admin",
    )

    source1 = create_source(
        name="source1",
        crawler_key="crawler1",
        scrape_interval_minutes=1,
        is_enabled=True,
    )
    response = await client.post("/sources", json=source1.model_dump(mode='json'))
    assert response.status_code == 201

    source2 = create_source(
        name="source2",
        crawler_key="crawler2",
        scrape_interval_minutes=1,
        is_enabled=True,
    )
    response = await client.post("/sources", json=source2.model_dump(mode='json'))
    assert response.status_code == 201

    response = await client.get("/sources")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
