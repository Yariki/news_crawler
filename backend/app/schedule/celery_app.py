from celery import Celery
from ..core.config import settings
import logging


logging.basicConfig(level=logging.DEBUG if settings.app_mode == "dev" else logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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

logging.info("Celery app configured and ready to run...")
