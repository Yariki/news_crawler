
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.messaging.handling_messages.handle_messages import handle_message
from app.messaging.rabbitmq_client import RabbitMQClient, get_rabbitmq_client
from app.services.es import ElasticService
import logging

from app.services.outbox_relay import OutboxRelay

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG if settings.app_mode != "prod" else logging.WARNING,  # Capture debug-level logs in non-prod environments
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

rabbitmq: RabbitMQClient | None = None



outbox_relay: OutboxRelay | None = None
outbox_relay_task: asyncio.Task | None = None

async def rabbitmq_connect(_app: FastAPI):
    """Connect to RabbitMQ and declare necessary infrastructure."""
    global rabbitmq
    rabbitmq = await get_rabbitmq_client()
    await rabbitmq.consume(settings.crawling_update_queue_name, handle_message)
    _app.state.rabbitmq = rabbitmq

@asynccontextmanager
async def lifespan(_app: FastAPI):
    global outbox_relay, outbox_relay_task
    """Lifespan function to initialize resources before the application starts."""
    elasticsearch_client = ElasticService()
    await elasticsearch_client.ensure_index()
    await rabbitmq_connect(_app)

    outbox_relay = OutboxRelay(elasticsearch_client, rabbitmq)
    outbox_relay_task = asyncio.create_task(outbox_relay.run_forever())

    try:
        yield
    finally:
        if outbox_relay:
            outbox_relay.stop()
        if outbox_relay_task:
            await outbox_relay_task
        if rabbitmq:
            await rabbitmq.close()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.app_mode != "prod" else None,
    redoc_url="/redoc" if settings.app_mode != "prod" else None,
    openapi_url="/openapi.json" if settings.app_mode != "prod" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
