import uuid

import pytest

from app.core.rbac import PermissionGranted
from app.models.status import Status
from app.repositories.crawljob_repository import CrawlJobRepository
from tests.conftest import set_authorization_context

async def test_create_source_and_crawl_job(client, db_session, create_source):

    context = await set_authorization_context(
        db_session,
        "source:read:own",
        "source:create:own",
        user_name="admin",
    )

    source = create_source(
        name="Test Source",
        crawler_key="test_crawler_key",
        scrape_interval_minutes=1,
        is_enabled=True,
    )

    response = await client.post("/sources", json=source.model_dump(mode='json'))

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == source.name
    
    source_id = data["id"]
    
    crawl_job = await CrawlJobRepository(db_session,PermissionGranted(auth=context, is_any=False)).create_crawl_job(source_id=source_id, status=Status.RUNNING)
    
    assert crawl_job is not None
    assert str(crawl_job.source_id) == source_id
    assert crawl_job.status == Status.RUNNING
    
    
async def test_create_source_and_crawl_job_with_invalid_source(client, db_session):

    context = await set_authorization_context(
        db_session,
        "source:read:own",
        "source:create:own",
        user_name="admin",
    )

    invalid_source_id = str(uuid.uuid4())  # Assuming this source ID does not exist

    with pytest.raises(ValueError) as exc_info:
        await CrawlJobRepository(db_session,PermissionGranted(auth=context, is_any=False)).create_crawl_job(source_id=invalid_source_id, status=Status.RUNNING)
    assert str(exc_info.value) == "Source not found"
        

async def test_source_run_crawl_job_twice(client, db_session, create_source):

    context = await set_authorization_context(
        db_session,
        "source:read:own",
        "source:create:own",
        user_name="admin",
    )

    payload = create_source(
        name="Test Source",
        crawler_key="test_crawler_key",
        scrape_interval_minutes=1,
        is_enabled=True,
    )

    response = await client.post("/sources", json=payload.model_dump(mode='json'))

    payload = payload.model_dump(mode='json')

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    
    source_id = data["id"]
    
    crawl_job1 = await CrawlJobRepository(db_session,PermissionGranted(auth=context, is_any=False)).create_crawl_job(source_id=source_id, status=Status.RUNNING)
    
    assert crawl_job1 is not None
    assert str(crawl_job1.source_id) == source_id
    assert crawl_job1.status == Status.RUNNING.value
    
    
    
    # Attempt to create another crawl job for the same source
    
    response = await client.post(f"/sources/{source_id}/run")
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["id"] == source_id
    assert data["detail"]["status"] == "error"
    assert "currently being crawled" in data["detail"]["message"]
    