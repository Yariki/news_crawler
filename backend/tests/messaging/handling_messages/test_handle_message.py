import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any
from uuid import uuid4

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from app.core.config import settings
from app.main import handle_message
from app.messaging.messages.base import MessageTypes
from app.messaging.rabbitmq_client import RabbitMQClient
from app.services.notifications import notification_hub


@pytest.fixture(scope="session")
def rabbitmq_url() -> Iterator[str]:
    rabbitmq = (
        DockerContainer("rabbitmq:3.13-management-alpine")
        .with_exposed_ports(5672)
        .waiting_for(LogMessageWaitStrategy("Server startup complete"))
    )
    with rabbitmq as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(5672)
        yield f"amqp://guest:guest@{host}:{port}/"


@pytest.fixture
async def rabbitmq_client(
    rabbitmq_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[RabbitMQClient]:
    suffix = uuid4().hex
    monkeypatch.setattr(settings, "rabbitmq_url", rabbitmq_url)
    monkeypatch.setattr(settings, "news_monitor_exchange_name", f"updates_{suffix}")
    monkeypatch.setattr(settings, "crawling_update_queue_name", f"updates_{suffix}")
    monkeypatch.setattr(settings, "dlx_name", f"dlx_{suffix}")
    monkeypatch.setattr(settings, "dlq_name", f"dlq_{suffix}")

    client = RabbitMQClient()
    await client.connect()
    await client.declare_infrastructure()
    try:
        yield client
    finally:
        await client.close()


@pytest.mark.integration
@pytest.mark.parametrize(
    "message",
    [
        {
            "id": "35cb0be7-15e9-4ef4-9ebf-82eb77a01f48",
            "type": MessageTypes.JOB_UPDATE.value,
            "job_id": "ebf69420-f0bb-4ec2-820f-572f7bdbe178",
            "status": "COMPLETED",
            "articles_found": 7,
            "articles_created": 5,
            "error_message": None,
            "started_at": "2026-06-25T10:00:00+00:00",
            "finished_at": "2026-06-25T10:01:00+00:00",
        },
        {
            "id": "865f77e5-01df-4d34-a088-05a59814d5a5",
            "type": MessageTypes.KEYWORDS_MATCH.value,
            "article_id": "e86f7819-3768-4eaa-a2c7-c9c50d18da41",
            "matched_keywords": ["security", "incident"],
            "title": "Security incident reported",
            "url": "https://example.com/security-incident",
            "published_at": "2026-06-25T10:00:00+00:00",
        },
    ],
    ids=["job-update", "keywords-match"],
)
async def test_handle_message_processes_messages_consumed_from_rabbitmq(
    rabbitmq_client: RabbitMQClient,
    message: dict[str, Any],
    mocker,
):
    processed = asyncio.Event()
    errors: list[BaseException] = []
    broadcast = mocker.patch.object(notification_hub, "broadcast")

    async def consume_message(payload: dict[str, Any]) -> None:
        try:
            await handle_message(payload)
        except BaseException as error:
            errors.append(error)
        finally:
            processed.set()

    await rabbitmq_client.consume(
        settings.crawling_update_queue_name,
        consume_message,
    )
    await rabbitmq_client.publish(message)
    await asyncio.wait_for(processed.wait(), timeout=5)

    if errors:
        raise errors[0]

    broadcast.assert_awaited_once_with(message["type"], message)
