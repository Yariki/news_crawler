import asyncio

from celery import Celery

from ..messaging.rabbitmq_client import RabbitMQClient
from ..core.config import settings

import logging

logging.basicConfig(
    level=logging.DEBUG if settings.app_mode != "prod" else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

rabbitmq_client = RabbitMQClient()

celery_app = Celery(
    "celery_app",
    broker=settings.celery_broker_url, 
    include=["app.schedule.tasks.dispatch_sources", "app.schedule.tasks.check_source"]
)

celery_app.conf.task_default_queue = settings.celery_task_queue
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_routes = {
    "schedule.tasks.run_scheduled_job": {"queue": settings.celery_task_queue},
}


async def _connect_rabbitmq():
    await rabbitmq_client.connect()
    await rabbitmq_client.declare_infrastructure()

asyncio.get_event_loop().run_until_complete(_connect_rabbitmq())