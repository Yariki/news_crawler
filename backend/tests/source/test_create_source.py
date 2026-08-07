from app.core.rbac import AuthorizationContext
from tests.conftest import set_authorization_context
import uuid

async def test_create_source(client, db_session, create_source):

    await set_authorization_context(
        db_session,
        "source:create:own",
        user_name="admin",
    )

    payload = create_source(
        name="Test Source",
        crawler_key="test_crawler_key",
        scrape_interval_minutes=1,
        is_enabled=True
    )

    response = await client.post("/sources", json=payload.model_dump(mode='json'))
    
    payload = payload.model_dump(mode='json')

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["language"] == payload["language"]
    assert data["source_type"] == payload["source_type"]
    assert data["crawler_key"] == payload["crawler_key"]
    assert data["scrape_interval_minutes"] == payload["scrape_interval_minutes"]
    assert data["is_enabled"] == payload["is_enabled"]
