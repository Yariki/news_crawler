import uuid

from fastapi import HTTPException
import pytest

from app.models.status import Status
from app.repositories.crawljob_repository import CrawlJobRepository
from tests.source.source_test_helper import create_source_payload


async def test_create_source_and_crawl_job(client, db_session):

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
    
    source_id = data["id"]
    
    crawl_job = await CrawlJobRepository(db_session).create_crawl_job(source_id=source_id, status=Status.RUNNING)
    
    assert crawl_job is not None
    assert str(crawl_job.source_id) == source_id
    assert crawl_job.status == Status.RUNNING.value
    
    
async def test_create_source_and_crawl_job_with_invalid_source(client, db_session):

    invalid_source_id = str(uuid.uuid4())  # Assuming this source ID does not exist

    with pytest.raises(ValueError) as exc_info:
        await CrawlJobRepository(db_session).create_crawl_job(source_id=invalid_source_id, status=Status.RUNNING)
    assert str(exc_info.value) == "Source not found"
        

async def test_source_run_crawl_job_twice(client, db_session):

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
    
    source_id = data["id"]
    
    crawl_job1 = await CrawlJobRepository(db_session).create_crawl_job(source_id=source_id, status=Status.RUNNING)
    
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
    