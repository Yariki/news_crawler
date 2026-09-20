from typing import Any

from celery import Celery
from celery.signals import worker_process_shutdown, worker_shutdown

from ..core.config import settings
from ..db.session import async_engine
from ..messaging.rabbitmq_client import close_rabbitmq_client
from .async_runner import runner
import logging


logging.basicConfig(level=logging.DEBUG if settings.app_mode == "dev" else logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

celery_app = Celery(
    "celery_app",
    broker=settings.rabbitmq_url,
    include=["app.schedule.tasks.dispatch_sources", "app.schedule.tasks.check_source"]
)

celery_app.conf.task_default_queue = settings.celery_task_queue
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_routes = {
    "schedule.tasks.run_scheduled_job": {"queue": settings.celery_task_queue},
}


async def _release_worker_resources() -> None:
    await close_rabbitmq_client()
    await async_engine.dispose()


@worker_process_shutdown.connect
@worker_shutdown.connect
def _shutdown_worker_loop(**_: Any) -> None:
    """Release the broker connection and DB pool on the worker loop, then stop it."""
    if not runner.is_running:
        # Nothing ran in this process (e.g. the prefork parent), so there is nothing to release.
        return
    try:
        runner.run(_release_worker_resources(), timeout=15.0)
    except Exception:
        logging.warning("Error releasing worker resources during shutdown", exc_info=True)
    runner.shutdown()


logging.info("Celery app configured and ready to run...")
