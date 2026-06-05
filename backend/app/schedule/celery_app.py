from celery import Celery
from ..core.config import settings

celery_app = Celery(
    "celery_app",
      broker=settings.celery_broker_url, 
      include=["app.schedule"]
)

celery_app.conf.task_default_queue = settings.celery_task_queue
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_routes = {
    "schedule.tasks.run_scheduled_job": {"queue": settings.celery_task_queue},
}
