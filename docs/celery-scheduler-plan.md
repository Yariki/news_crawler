# Rework Celery Scheduler Plan for In-Backend Celery

## Summary
Rewrite `docs/celery-scheduler-plan.md` so the scheduler is no longer a separate `scheduler_service/`. The same `backend` project will own the FastAPI app, Celery app, Celery worker, Celery beat scheduler, and crawl tasks. RabbitMQ remains the Celery broker.

The runtime architecture becomes:

- `backend` FastAPI process: API only, no APScheduler.
- `backend` Celery worker process: executes crawl tasks.
- `backend` Celery beat process: schedules periodic crawl tasks.
- RabbitMQ: broker for scheduled and manual crawl queues.
- Postgres: existing application database and crawl history.

## Key Changes
- Replace the “New Service Directory” section with an in-backend layout:
  - `backend/app/celery_app.py`
  - `backend/app/tasks/crawl_tasks.py`
  - `backend/app/tasks/scheduler_tasks.py` or beat configuration module
  - optional `backend/app/services/celery_client.py`
- Remove the separate `scheduled_sources` projection model, separate scheduler DB schema, separate Alembic setup, event consumer, and source lifecycle event projection.
- Use the existing `sources` table as the schedule source of truth.
- Configure Celery beat from the backend codebase to enqueue crawl tasks for enabled sources.
- Keep RabbitMQ queues:
  - `crawl.default` for periodic crawls
  - `crawl.run_now` for manual crawls
- Remove APScheduler usage from `backend/app/services/scheduler.py` and `backend/app/main.py`.

## Implementation Changes
- Add Celery to `backend/requirements.txt`:
  - `celery[rabbitmq]==5.*`
- Remove:
  - `apscheduler==3.10.4`
- Add `rabbitmq_url` to `backend/app/core/config.py`, mapped from `RABBITMQ_URL`.
- Create a backend Celery app configured with:
  - RabbitMQ broker
  - no result backend
  - `task_ignore_result=True`
  - `task_acks_late=True`
  - `worker_prefetch_multiplier=1`
  - task routes for `crawl.default` and `crawl.run_now`
- Implement `crawl.run_crawl(source_id: str, trigger: str = "scheduled")` inside backend tasks.
  - Open an `AsyncSessionLocal`.
  - Load the authoritative `Source`.
  - Select the right crawler using the existing crawler logic.
  - Run the async crawl from the synchronous Celery task with `asyncio.run(...)`.
  - Add a per-source lock to prevent manual and scheduled crawls from overlapping.
- Replace `POST /api/sources/{source_id}/run`.
  - Validate the source exists.
  - Publish `crawl.run_crawl` to `crawl.run_now`.
  - Return `{"id": source_id, "status": "queued", "task_id": task.id}`.
  - Update `SourceRunResponse` to include optional `task_id`.
- Replace APScheduler startup in `backend/app/main.py`.
  - Keep Elasticsearch initialization.
  - Remove `refresh_scheduler_jobs()`, `scheduler.start()`, and `scheduler.shutdown()`.
- For periodic scheduling, prefer a small custom Celery beat scheduler that reads enabled rows from `sources`.
  - Beat selects enabled sources due for execution.
  - It enqueues `crawl.run_crawl`.
  - It must avoid duplicate enqueueing if beat restarts.
  - If persistence requires a DB field, add a migration for `sources.next_run_at` or a small `scheduled_crawls` table inside the existing backend migrations.
- Update `docker-compose.yml`.
  - Add RabbitMQ with management UI.
  - Add `RABBITMQ_URL` to backend environment.
  - Add `celery_worker` service using the existing `backend` image/context.
  - Add `celery_beat` service using the existing `backend` image/context.
  - Add `rabbitmq_data` volume.
- Do not create `scheduler_service/`, a second requirements file, a second Dockerfile, or a second Alembic environment.

## Test Plan
- Unit test Celery task routing/configuration where practical.
- Unit test `run_crawl` dispatches to the existing crawler flow and handles missing sources.
- API test `/api/sources/{id}/run` returns `queued` and publishes a Celery task.
- Scheduler test verifies only enabled sources are enqueued.
- Scheduler test verifies due-time calculation does not enqueue duplicates across beat ticks.
- Compose smoke test:
  - RabbitMQ starts.
  - Backend starts without APScheduler.
  - Celery worker consumes `crawl.run_now`.
  - Celery beat enqueues periodic crawl tasks.

## Assumptions
- The user wants one backend codebase and image, with separate runtime commands for API, worker, and beat.
- RabbitMQ remains the only broker.
- Celery results are not stored; crawl visibility remains in the existing `crawl_jobs` table.
- Manual runs do not reset the periodic schedule.
- Source create/update/delete event projection is out of scope because scheduling now reads from the existing backend database directly.
