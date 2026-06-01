# Celery Scheduler Service — Implementation Plan

## Context & Motivation

The current architecture embeds APScheduler inside the FastAPI process (`backend/app/services/scheduler.py`). On startup, it reads all enabled `Source` rows from Postgres and registers interval jobs. The `POST /api/sources/{id}/run` endpoint triggers an immediate execution by mutating the job's `next_run_time`.

This plan replaces APScheduler with a dedicated, independently deployable **scheduler service** backed by Celery + RabbitMQ. The API service is decoupled from crawl execution: it publishes durable source lifecycle events and run-now commands; the scheduler service owns the periodic schedule; worker processes execute crawls.

Primary goals:

- allow multiple API replicas without duplicate scheduled crawls;
- keep the API fast by queueing crawl work;
- make scheduling state observable and recoverable after restarts;
- preserve the existing crawler implementation while moving orchestration out of FastAPI.

---

## High-Level Architecture

```
┌────────────────┐ source events/run_now ┌────────────────────┐
│ API (FastAPI)  │──────────────────────▶│ RabbitMQ broker     │
│                │                       │ queues:             │
│ source CRUD    │                       │ - scheduler.events  │
│ POST /run      │                       │ - crawl.default     │
└────────────────┘                       │ - crawl.run_now     │
                                         └─────────┬──────────┘
                                                   │
                         ┌─────────────────────────┼─────────────────────────┐
                         │                         │                         │
              ┌──────────▼──────────┐   ┌──────────▼──────────┐   ┌──────────▼──────────┐
              │ scheduler_consumer  │   │ celery beat          │   │ celery_worker       │
              │ applies source      │   │ polls schedule DB    │   │ executes backend    │
              │ events to DB        │   │ enqueues crawls      │   │ crawler services    │
              └──────────┬──────────┘   └──────────┬──────────┘   └─────────────────────┘
                         │                         │
                         └──────────┬──────────────┘
                                    ▼
                         ┌────────────────────┐
                         │ scheduled_sources  │
                         │ scheduler schema   │
                         └────────────────────┘
```

Recommended default: implement a small custom Celery Beat scheduler that reads `scheduled_sources` and emits `crawl.run_crawl` tasks. Avoid maintaining two sources of schedule truth (`scheduled_sources` plus Celery Beat's own periodic-task tables) unless there is a strong need for a generic periodic-task UI.

---

## 1. New Service Directory

Create a top-level `scheduler_service/` directory alongside `backend/` and `frontend/`. This service owns its Celery app, event projection model, Beat scheduler, and migrations. The crawl worker still imports the existing `backend` package because the crawler services currently live there.

```
scheduler_service/
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── migrations/
│   └── versions/
├── app/
│   ├── celery_app.py           # Celery instance, broker/backend config, autodiscover
│   ├── config.py               # Settings (DB URL, RabbitMQ URL, env vars)
│   ├── db/
│   │   ├── base.py             # DeclarativeBase
│   │   └── session.py          # Sync SQLAlchemy session for scheduler projection DB
│   ├── models/
│   │   └── scheduled_source.py # ScheduledSource table (see §2)
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── crawl_tasks.py      # run_crawl task; wraps existing async crawlers
│   │   └── event_tasks.py      # source created/updated/deleted event handlers
│   └── beat/
│       └── scheduler.py        # Custom beat scheduler that reads ScheduledSource table
```

For the first implementation, build the Celery worker image from the repository root and install/copy both `backend/` and `scheduler_service/`. Bind mounts are fine for local development, but the production image must include both packages. A later cleanup can extract crawlers into a shared `crawler_lib/` package if the scheduler and API start diverging.

---

## 2. ScheduledSource Model

The scheduler service maintains its own `scheduled_sources` table. It is a **denormalized projection** of the API's `sources` table, populated through events. The scheduler projection should contain only fields needed to decide when to enqueue a crawl; the crawl task can load the authoritative source row from the backend DB when it executes.

| Column                    | Type        | Notes                                            |
|---------------------------|-------------|--------------------------------------------------|
| `id`                      | UUID PK     | Same UUID as `sources.id` in API DB              |
| `base_url`                | String(500) | Optional diagnostic copy; task should not trust it as authoritative |
| `source_type`             | Integer     | Maps to `SourceType`; useful for filtering unsupported sources early |
| `scrape_interval_minutes` | Integer     | Add a positive check constraint                  |
| `is_enabled`              | Boolean     | Disabled sources are not scheduled               |
| `source_updated_at`       | DateTime    | Source row timestamp from API event; ignore older events |
| `last_enqueued_at`        | DateTime    | Last periodic task enqueue time                  |
| `next_run_at`             | DateTime    | Persisted next due time to avoid restart stampedes |
| `created_at`              | DateTime    | Scheduler projection timestamp                   |
| `updated_at`              | DateTime    | Scheduler projection timestamp                   |

Do **not** store `celery_task_id` unless the implementation chooses to use Celery Beat's periodic-task tables. With the recommended custom scheduler, Beat reads due rows directly from `scheduled_sources`, enqueues tasks, and updates `last_enqueued_at` / `next_run_at`.

Migration: Alembic inside `scheduler_service/migrations/`. The simplest deployment is the same Postgres instance with a separate schema named `scheduler`. A separate database is also valid if operational isolation matters more than local simplicity.

Bootstrap requirement: existing rows in `sources` will not appear in `scheduled_sources` automatically. Add a one-time `sync-sources` command or API endpoint that publishes a full source snapshot before disabling APScheduler in production.

---

## 3. Celery Configuration

**Broker:** `amqp://crawler:crawler_pass@rabbitmq:5672//`  
**Result backend:** not required. Prefer `result_backend = None` and `task_ignore_result = True`; use the existing `crawl_jobs` table for user-visible job history instead of Celery result storage.

**Queues:**

| Queue name          | Purpose                                           |
|---------------------|---------------------------------------------------|
| `scheduler.events`  | Source lifecycle events from API                  |
| `crawl.default`     | Periodic crawl tasks dispatched by Beat           |
| `crawl.run_now`     | On-demand crawl tasks from the `/run` endpoint    |

Declare these queues as durable and publish persistent messages. With `task_acks_late = True`, crawl tasks must be idempotent because a worker crash can cause RabbitMQ to redeliver a task.

Beat and workers are separate processes; workers can be scaled horizontally. Beat is a singleton. In Kubernetes, keep the Beat deployment at one replica or add a database/advisory-lock leader guard.

Recommended Celery settings:

```python
broker_url = settings.rabbitmq_url
result_backend = None
task_ignore_result = True
broker_connection_retry_on_startup = True
task_acks_late = True
worker_prefetch_multiplier = 1
task_time_limit = 30 * 60
task_soft_time_limit = 25 * 60

task_routes = {
    "scheduler.source_created": {"queue": "scheduler.events"},
    "scheduler.source_updated": {"queue": "scheduler.events"},
    "scheduler.source_deleted": {"queue": "scheduler.events"},
    "crawl.run_crawl": {"queue": "crawl.default"},
}
```

Use `.apply_async(queue="crawl.run_now")` for run-now requests so manual crawls do not wait behind the normal periodic queue. If manual runs must always jump ahead, add a small dedicated worker for `crawl.run_now` instead of relying only on queue order.

**Beat scheduler:** implement a custom `DatabaseScheduler` backed by `scheduled_sources`. On each tick, it selects enabled rows where `next_run_at <= now()`, enqueues `crawl.run_crawl(source_id=...)`, then advances `next_run_at` by `scrape_interval_minutes`. Keep `beat_max_loop_interval` low enough for acceptable schedule latency, for example 5-30 seconds.

---

## 4. Task Definitions

### `crawl_tasks.py` — `run_crawl`

```
run_crawl(source_id: str, trigger: str = "scheduled")
```

- Routes to `crawl.default` for periodic work or `crawl.run_now` for immediate work.
- Loads the authoritative `Source` row from the backend DB by `source_id`; do not rely on `base_url` or `source_type` copied into the queue payload.
- Wraps the existing async crawler code with `asyncio.run(...)` and uses the existing backend `AsyncSessionLocal`.
- Acquires a per-source lock before crawling so a slow periodic crawl and a run-now crawl cannot process the same source concurrently. A PostgreSQL advisory lock keyed by `source_id` is enough for the first version.
- Records crawl progress in the existing `crawl_jobs` table. For better queued-state visibility, create a `WAITING` job in the API before publishing and pass `job_id` to the task; otherwise the job appears only after a worker starts it.

### `event_tasks.py` — source lifecycle handlers

```
source_created(source_id, base_url, scrape_interval_minutes, source_type, is_enabled, source_updated_at)
source_updated(source_id, changed_fields, source_updated_at)
source_deleted(source_id, source_updated_at)
```

All three consume from `scheduler.events`. They upsert/delete the `ScheduledSource` row only; they should not call Beat directly. Beat notices changes by polling the scheduler DB.

Handlers must be idempotent:

- duplicate create/update events should be harmless;
- update/delete events older than `source_updated_at` already stored in `scheduled_sources` should be ignored;
- delete can either remove the projection row or mark `is_enabled = false`.

---

## 5. API Service Changes

### 5.1 Remove APScheduler

- Delete `backend/app/services/scheduler.py`.
- Remove `refresh_scheduler_jobs()` and `scheduler.start()` / `scheduler.shutdown()` from `backend/app/main.py` lifespan.
- Remove `apscheduler` from `backend/requirements.txt`.

### 5.2 Add Celery Client

Add a thin `backend/app/celery_client.py` that creates a Celery app instance configured only with the broker URL. No worker runs inside the API process, and the API should not import task implementations. It only publishes task names with `.send_task()` / `.apply_async()`.

Recommended reliability path: add an API-side transactional outbox table for source lifecycle events. `create_source()` / `update_source()` commit the source row and outbox event in the same transaction; a small publisher process drains the outbox to RabbitMQ and marks events delivered. Direct publish after commit is simpler, but it can permanently lose a scheduler event if RabbitMQ is unavailable at the wrong moment.

### 5.3 Source Create / Update Hooks

This is the mandatory integration point between the API and the scheduler service: every source create/update that changes scheduling data must publish a source lifecycle event to RabbitMQ queue `scheduler.events`. The scheduler service consumes those events and updates its `scheduled_sources` projection.

Keep the publish logic behind a small backend helper, for example `backend/app/services/source_events.py`, so `SourceService` does not know Celery details:

```python
class SourceEventPublisher:
    def publish_created(self, source: Source) -> None: ...
    def publish_updated(self, source: Source, changed_fields: dict) -> None: ...
```

In `SourceService.create_source()` — after the source row is committed and refreshed, publish `scheduler.source_created` or write the same payload to an outbox:

```python
celery_client.send_task(
    "scheduler.source_created",
    kwargs={
        "source_id": str(source.id),
        "base_url": source.base_url,
        "source_type": int(source.source_type),
        "scrape_interval_minutes": source.scrape_interval_minutes,
        "is_enabled": source.is_enabled,
        "source_updated_at": source.updated_at.isoformat(),
    },
    queue="scheduler.events",
)
```

Add `update_source()` to `SourceService` and `PATCH /api/sources/{source_id}` to `backend/app/api/source/api.py` (currently missing). After the update is committed and refreshed, publish `scheduler.source_updated` when any scheduler-relevant field changes: `base_url`, `source_type`, `scrape_interval_minutes`, or `is_enabled`.

```python
celery_client.send_task(
    "scheduler.source_updated",
    kwargs={
        "source_id": str(source.id),
        "changed_fields": changed_fields,
        "source_updated_at": source.updated_at.isoformat(),
    },
    queue="scheduler.events",
)
```

If an update changes only non-scheduling fields such as `name` or `language`, the scheduler event can be skipped unless those fields are later added to the scheduler projection.

Add a delete/disable path as well. If the product does not need hard deletes yet, treating `is_enabled=false` as the delete signal is enough for the scheduler.

### 5.4 Run-Now Endpoint

Replace the current APScheduler-based `run_scheduled_job()` call in `POST /api/sources/{id}/run` with:

```python
celery_client.send_task(
    "crawl.run_crawl",
    kwargs={"source_id": source_id, "trigger": "manual"},
    queue="crawl.run_now",
)
```

The API should fetch the source first to return `404` for unknown IDs and decide whether disabled sources can be run manually. Return `{"id": source_id, "status": "queued", "task_id": task.id}` immediately. Update `SourceRunResponse` if the task ID is returned.

---

## 6. Docker Compose Changes

### 6.1 Add RabbitMQ

```yaml
rabbitmq:
  image: rabbitmq:3.13-management
  environment:
    RABBITMQ_DEFAULT_USER: crawler
    RABBITMQ_DEFAULT_PASS: crawler_pass
  healthcheck:
    test: ["CMD", "rabbitmq-diagnostics", "ping"]
    interval: 10s
    timeout: 5s
    retries: 10
  ports:
    - "5672:5672"    # AMQP
    - "15672:15672"  # Management UI (dev only)
  volumes:
    - rabbitmq_data:/var/lib/rabbitmq
```

### 6.2 Celery Worker Service

```yaml
celery_worker:
  build:
    context: .
    dockerfile: scheduler_service/Dockerfile
  command: celery -A scheduler_service.app.celery_app worker --loglevel=info -Q crawl.run_now,crawl.default --concurrency=4
  environment:
    DATABASE_URL: postgresql+asyncpg://news_user:news_password@postgres:5432/news_monitor
    SCHEDULER_DATABASE_URL: postgresql+psycopg://news_user:news_password@postgres:5432/news_monitor
    RABBITMQ_URL: amqp://crawler:crawler_pass@rabbitmq:5672//
    ELASTICSEARCH_URL: http://elasticsearch:9200
  depends_on:
    postgres:
      condition: service_healthy
    rabbitmq:
      condition: service_healthy
    elasticsearch:
      condition: service_healthy
  volumes:
    - ./backend:/srv/backend
    - ./scheduler_service:/srv/scheduler_service
```

The worker image must include both packages. A suitable `scheduler_service/Dockerfile` can copy `backend/requirements.txt`, `scheduler_service/requirements.txt`, `backend/`, and `scheduler_service/`, then set `PYTHONPATH=/srv/backend:/srv`.

### 6.3 Celery Beat Service

```yaml
celery_beat:
  build:
    context: .
    dockerfile: scheduler_service/Dockerfile
  command: >
    sh -c "cd /srv/scheduler_service &&
           alembic upgrade head &&
           celery -A scheduler_service.app.celery_app beat --loglevel=info --scheduler scheduler_service.app.beat.scheduler:DatabaseScheduler"
  environment:
    SCHEDULER_DATABASE_URL: postgresql+psycopg://news_user:news_password@postgres:5432/news_monitor
    RABBITMQ_URL: amqp://crawler:crawler_pass@rabbitmq:5672//
  depends_on:
    postgres:
      condition: service_healthy
    rabbitmq:
      condition: service_healthy
  volumes:
    - ./scheduler_service:/srv/scheduler_service
```

### 6.4 Event Consumer (optional separate process)

The source lifecycle tasks can run on the worker or on a dedicated lightweight consumer:

```yaml
scheduler_consumer:
  build:
    context: .
    dockerfile: scheduler_service/Dockerfile
  command: celery -A scheduler_service.app.celery_app worker --loglevel=info -Q scheduler.events --concurrency=1
  environment:
    SCHEDULER_DATABASE_URL: postgresql+psycopg://news_user:news_password@postgres:5432/news_monitor
    RABBITMQ_URL: amqp://crawler:crawler_pass@rabbitmq:5672//
  depends_on:
    postgres:
      condition: service_healthy
    rabbitmq:
      condition: service_healthy
```

### 6.5 Backend Service — add RabbitMQ dependency

```yaml
backend:
  ...
  environment:
    ...
    RABBITMQ_URL: amqp://crawler:crawler_pass@rabbitmq:5672//
  depends_on:
    postgres:
      condition: service_healthy
    elasticsearch:
      condition: service_healthy
    rabbitmq:
      condition: service_healthy
```

### 6.6 New volume

```yaml
volumes:
  postgres_data:
  es_data:
  rabbitmq_data:    # add this
```

---

## 7. Startup & Bootstrap Flow

1. Deploy RabbitMQ and the scheduler DB schema first.
2. Run `scheduler_service` Alembic migrations to create the `scheduler.scheduled_sources` table.
3. Backfill existing API `sources` rows into `scheduled_sources` with a one-time `sync-sources` command or by asking the API to publish a full source snapshot.
4. Start `scheduler_consumer`; it consumes source lifecycle events and keeps `scheduled_sources` current.
5. Start `celery_beat`; the custom scheduler polls enabled due rows and enqueues `crawl.run_crawl` to `crawl.default`.
6. Start `celery_worker`; it consumes `crawl.default` and `crawl.run_now`, acquires the per-source lock, and calls the existing crawler service.
7. Remove APScheduler startup from the API only after the backfill and Beat worker are verified. This avoids a gap where no existing sources are scheduled.
8. When a user creates or updates a source, the API commits the row and emits/outboxes a source event. Beat sees the projection change on its next poll.
9. When a user clicks "Run Now", the API publishes `crawl.run_crawl` directly to `crawl.run_now`; this should not mutate the periodic `next_run_at` unless the product explicitly wants manual runs to reset the schedule.

---

## 8. Dependency Changes

### `backend/requirements.txt` additions
```
celery[rabbitmq]==5.*
```

Remove:
```
apscheduler==3.10.4
```

### `scheduler_service/requirements.txt`
```
celery[rabbitmq]==5.*
sqlalchemy==2.0.*
psycopg[binary]==3.2.*
alembic==1.*
pydantic-settings==2.*
```

Do not list `kombu` separately unless a compatibility issue requires pinning it; Celery already depends on it. Do not add `celery-sqlalchemy-scheduler` for the recommended custom scheduler. If you choose that library instead, remove `next_run_at` ownership from `scheduled_sources` and let the library's periodic-task tables become the source of truth.

---

## 9. Implementation Order

1. **Infrastructure** — Add RabbitMQ to `docker-compose.yml`, verify broker connectivity from backend and scheduler containers.
2. **Scheduler service scaffold** — Create `scheduler_service`, config, `celery_app.py`, Dockerfile, empty task modules, and Alembic wiring.
3. **ScheduledSource model + migration** — Create the scheduler schema/table and add constraints/indexes on `is_enabled`, `next_run_at`, and `source_updated_at`.
4. **Event tasks** — Implement idempotent `source_created`, `source_updated`, and `source_deleted` projection handlers.
5. **Bootstrap sync** — Add a one-time command or API-driven job to backfill all current sources before cutting over.
6. **Beat scheduler** — Implement DB-backed due-row polling and `next_run_at` advancement.
7. **Crawl task** — Implement `run_crawl(source_id, trigger)` around the existing async crawler classes, including per-source locking.
8. **API event publishing** — Add Celery client and source create/update/delete event publication; prefer a transactional outbox if time allows.
9. **Run-now endpoint** — Replace `run_scheduled_job()` with a direct Celery publish to `crawl.run_now`; return queued status and task ID.
10. **Remove APScheduler** — Delete API lifespan scheduler startup and remove `apscheduler` dependency after the Celery path is verified.
11. **Docker services** — Add `celery_worker`, `celery_beat`, and `scheduler_consumer`; update backend `RABBITMQ_URL` dependency.
12. **Tests** — Add unit tests for event idempotency and scheduler due-row calculation, plus an integration test for create source -> scheduled projection -> task enqueue and `/run` -> immediate enqueue.

---

## 10. Open Questions / Decisions

| # | Question | Options |
|---|----------|---------|
| 1 | Worker image: shared with backend or separate? | Recommended first step: one scheduler worker image built from repo root that includes both `backend/` and `scheduler_service/` |
| 2 | Scheduler DB: same Postgres instance (separate schema) or separate DB? | Same instance, schema `scheduler` is simplest for single-server deployment |
| 3 | Result backend needed? | No for first implementation; use `crawl_jobs` for user-visible state |
| 4 | Source delete event? | API currently has no DELETE endpoint; add one or handle via `is_enabled=false` |
| 5 | Celery Beat library: `celery-sqlalchemy-scheduler` vs custom? | Recommended: custom scheduler because this app only needs interval schedules from one projection table |
| 6 | Should a newly created source crawl immediately? | Choose explicitly: `next_run_at = now()` for fast feedback, or `now() + interval` to avoid surprise load |
| 7 | Should manual run reset the periodic schedule? | Recommended: no; run-now is an extra execution and should not mutate `next_run_at` |
| 8 | How reliable must source event delivery be? | Direct publish is acceptable for a prototype; transactional outbox is safer for production |

---

## 11. Additional Suggestions

- Add a per-source PostgreSQL advisory lock in `run_crawl` before invoking crawlers. This prevents duplicate work when a periodic task, a retry, and a manual run overlap.
- Add validation on `SourceCreateUpdate.scrape_interval_minutes` to reject zero or negative intervals before they reach the scheduler.
- Add metrics/logs for `scheduled_sources` lag: due rows count, last Beat tick, event consumer failures, task enqueue failures, and per-source skipped crawls due to lock contention.
- Keep `scheduler_consumer` separate from crawl workers in production. Source updates should not be delayed by long crawls.
- Update README and Kubernetes notes after cutover; they currently warn that APScheduler requires `backend.replicaCount=1`.
