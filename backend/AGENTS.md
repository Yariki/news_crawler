# AGENTS.md

## Big Picture
- This is a FastAPI backend for a news monitoring pipeline: persist sources/articles/jobs in PostgreSQL, index/search articles in Elasticsearch, and push keyword alerts over WebSocket.
- App startup (`app/main.py`) is lightweight: the lifespan hook only ensures the Elasticsearch `articles` index exists before serving requests.
- API routing is centralized under `/api` in `app/api/routes.py` and currently exposes `keywords`, `sources`, `dashboard`, `health`, `articles`, and `ws`. The `messages` router is mounted only when `APP_MODE == "dev"`.
- Background crawling is driven by the scheduling layer under `app/schedule/**`: a polling beat loop (`app/schedule/celery_beat.py`) finds due sources, enqueues Celery tasks, then source-type-specific crawler services do the actual fetch/store/index/notify work.

## Service Boundaries And Data Flow
- Route handlers are mostly thin, but the split is not uniform: `SourceService` and `DashboardService` own their DB logic, while `keywords` routes call the repository directly.
- Source scheduling state lives on the `Source` model. `SourceService.create_source()` normalizes `base_url`, preserves `scrape_interval_minutes`, and initializes `next_run_at` to `utc_now()` so new enabled sources are immediately eligible for dispatch.
- Due-source dispatch lives in `app/schedule/tasks/dispatch_sources.py`: it loads enabled sources whose `next_run_at <= now`, enqueues `run_scheduled_job.delay(...)`, then advances each source's `next_run_at` by `scrape_interval_minutes` after enqueueing.
- Celery execution fans into `app/schedule/tasks/check_source.py`, where the `switcher` maps `SourceType` to crawler service classes: `HtmlCrawlService`, `RssCrawlService`, and `TelegramCrawlerService`.
- `BaseCrawler` owns the shared pipeline for HTML/RSS-style sources: load enabled keywords, fetch/cache `robots.txt`, honor crawl delay, discover candidate URLs, dedupe against existing article URLs, persist articles and keyword hits, index into Elasticsearch, and broadcast alerts.
- `TelegramCrawlerService` is a separate flow built around `TelegramScrapper`: it reads incremental messages using `Source.last_message_id`, creates articles directly from channel messages, updates `last_message_id`, indexes matching content, and emits notifications for alerts.
- Keyword loading still falls back to `settings.default_keywords_list` when there are no enabled DB keywords (`app/services/crawlers/base_crawler.py`).
- Elasticsearch integration is wrapped in `ElasticService` (`app/services/es.py`). Current code instantiates `ElasticService()` where needed instead of using a shared singleton.
- WebSocket alert fan-out goes through the module-level `notification_hub` in `app/services/notifications.py`, and clients connect via `/api/ws/alerts`.

## Project-Specific Conventions
- IDs are UUIDs at the DB/model level via `PrimaryIdMixin` (`app/db/base.py`). Response models serialize them; the only notable manual string conversion in the API surface is the async task payload/response path such as `SourceRunResponse`.
- `source_type` and crawl job `status` are `IntEnum` values (`app/models/source_type.py`, `app/models/status.py`), not string enums.
- Source types supported by the scheduling/crawl path today are `NEWS_SITE`, `RSS`, and `TELEGRAM_CHANNEL`. Other enum members exist but are not wired into the task switcher.
- Source scheduling depends on `next_run_at` plus `scrape_interval_minutes`. Any feature that changes dispatch timing needs to keep those two fields and `dispatch_due_sources()` in sync.
- Keyword matching uses `normalize_keyword()` plus boundary-aware regex detection in `detect_keywords()` (`app/services/keyword_detector.py`).
- HTML/RSS dedupe is URL-based before article creation. Telegram dedupe is also URL-based, where the URL is derived from the channel username and Telegram message id.
- Environment file selection is `APP_MODE`-driven via `app/core/env_settings.py`: prod loads `.env`, and non-prod modes load `.env-<mode>`.
- Telegram crawling is non-interactive in workers. The Telethon session must be authorized in advance with `scripts/telegram_authorize.py`.

## Critical Workflows
- Install deps:
  - `pip install -r requirements.txt`
  - `pip install -r requirements-dev.txt`
- Run API locally (dev mode enables docs and mounts the dev-only messages route):
  - `APP_MODE=dev uvicorn app.main:app --reload`
- Run the Celery worker used by source dispatch/run endpoints:
  - `celery -A app.schedule.celery_app.celery_app worker --loglevel=info`
- Run the polling beat loop that finds due sources and enqueues crawl tasks:
  - `APP_MODE=dev python -m app.schedule.celery_beat`
- Authorize the Telegram session once before enabling Telegram sources:
  - `python scripts/telegram_authorize.py`
- Run tests (pytest config in `pyproject.toml`; tests use Postgres testcontainer + Alembic in `tests/conftest.py`):
  - `pytest`
- Run migrations:
  - `alembic upgrade head`
  - `alembic revision --autogenerate -m "<message>" --rev-id "<message>"`

## Integration Points To Respect
- PostgreSQL is required for sources, crawl jobs, articles, keyword hits, and cached robots data.
- RabbitMQ or another Celery-compatible broker must be available for async crawl dispatch; both `dispatch_due_sources()` and `POST /api/sources/{source_id}/run` enqueue Celery tasks.
- Elasticsearch index name is fixed as `articles` (`app/services/es.py`); the `/api/articles/search` endpoint depends on that mapping.
- RSS parsing uses `feedparser`; HTML parsing uses BeautifulSoup + lxml; HTTP fetches use `httpx.AsyncClient`.
- Robots support is now part of the HTML/RSS crawl path: `RobotsService.fetch_robot()` caches `robots.txt` in the database, refreshes stale rows after 7 days, and `BaseCrawler` currently enforces crawl delay from that data. `can_fetch()` and request-rate values are available but not enforced in the crawl loop yet.
- Telegram crawling depends on `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and a pre-authorized local session file.

## Safe Change Patterns
- When adding or changing source-type behavior, update all three layers that currently participate in dispatch: the Celery `switcher` in `app/schedule/tasks/check_source.py`, the scraper mapping in `app/services/crawlers/base_crawler.py` if applicable, and the crawler/scraper implementation itself.
- If you change scheduling semantics, keep `Source.next_run_at`, `scrape_interval_minutes`, `dispatch_due_sources()`, and the manual `/sources/{id}/run` endpoint behavior aligned.
- Keep API changes aligned with existing tests under `tests/source/*`, `tests/keywords/*`, and `tests/test_shealth_api.py`.
- Follow the local abstraction that already owns the data path instead of forcing a new layer. Today that usually means service classes for `source` and `dashboard`, repositories for `keywords`, and crawler classes for ingestion logic.

