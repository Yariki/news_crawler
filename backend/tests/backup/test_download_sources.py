import json

from tests.conftest import set_authorization_context


EXPORTED_FIELDS = {
    "base_url",
    "name",
    "language",
    "source_type",
    "crawler_key",
    "scrape_interval_minutes",
    "is_enabled",
}


async def test_download_sources_success(db_session, client, create_source):

    await set_authorization_context(
        db_session,
        "source:read:own",
        "source:create:own",
        user_name="admin",
    )

    source1 = create_source(
        name="source1",
        base_url="https://example1.com",
        crawler_key="crawler1",
        scrape_interval_minutes=15,
        is_enabled=True,
    )
    source2 = create_source(
        name="source2",
        base_url="https://example2.com",
        crawler_key="crawler2",
        scrape_interval_minutes=30,
        is_enabled=False,
    )
    for source in (source1, source2):
        response = await client.post("/sources", json=source.model_dump(mode='json'))
        assert response.status_code == 201

    response = await client.get("/backup/sources/download")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["content-disposition"] == 'attachment; filename="sources.json"'

    data = json.loads(response.content)
    assert isinstance(data, list)
    assert len(data) == 2

    by_name = {item["name"]: item for item in data}
    assert set(by_name) == {"source1", "source2"}
    for item in data:
        assert set(item) == EXPORTED_FIELDS

    assert by_name["source1"]["crawler_key"] == "crawler1"
    assert by_name["source1"]["scrape_interval_minutes"] == 15
    assert by_name["source1"]["is_enabled"] is True
    assert by_name["source1"]["source_type"] == source1.source_type
    assert by_name["source2"]["crawler_key"] == "crawler2"
    assert by_name["source2"]["scrape_interval_minutes"] == 30
    assert by_name["source2"]["is_enabled"] is False


async def test_download_sources_empty(db_session, client):

    await set_authorization_context(
        db_session,
        "source:read:own",
        user_name="admin",
    )

    response = await client.get("/backup/sources/download")

    assert response.status_code == 200
    assert json.loads(response.content) == []


async def test_download_sources_only_own(db_session, client, create_source, create_user):

    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    other_user = create_user()
    response = await client.post("/admin/users", json=other_user.model_dump(mode='json'))
    assert response.status_code == 201

    response = await client.post("/sources", json=create_source(name="admin_source").model_dump(mode='json'))
    assert response.status_code == 201

    await set_authorization_context(
        db_session,
        "source:read:own",
        user_name=other_user.username,
        role="user",
    )

    response = await client.get("/backup/sources/download")

    assert response.status_code == 200
    assert json.loads(response.content) == []


async def test_download_sources_forbidden(db_session, client):

    await set_authorization_context(
        db_session,
        "keyword:read:own",
        user_name="admin",
        role="user",
    )

    response = await client.get("/backup/sources/download")

    assert response.status_code == 403
