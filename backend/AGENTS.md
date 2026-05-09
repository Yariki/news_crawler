# AGENTS.md

## Big Picture
- This is a FastAPI backend for a news monitoring pipeline: crawl sources, persist articles/jobs in PostgreSQL, index/search in Elasticsearch, and broadcast keyword alerts over WebSocket.
- App startup (`app/main.py`) runs a lifespan hook that ensures the Elasticsearch index exists, reloads APScheduler jobs from DB, then starts the scheduler.
- API routing is centralized under `/api` in `app/api/routes.py`, then split by domain: `keywords`, `sources`, `dashboard`.
- Crawling flow is orchestrated by scheduler jobs (`app/services/scheduler.py`) -> crawler services (`app/services/crawlers/*.py`) -> scrapers (`app/scrapers/**`) -> DB + Elasticsearch + notifications.

## Service Boundaries And Data Flow
- API layer (`app/api/**/api.py`) is intentionally thin: parse request, call a service, manually shape response dicts.
- Domain services in `app/api/**/services/*.py` own DB queries/commits and raise `HTTPException` for not-found behaviors.
- Crawler services (`HtmlCrawlService`, `RssCrawlService`) extend `BaseCrawler` and are the only place that performs full pipeline work (source lookup, dedupe by URL, keyword detection, keyword hit rows, ES index, WS alert).
- `BaseCrawler._get_keywords()` falls back to `settings.default_keywords_list` if no enabled DB keywords (`app/services/crawlers/base_crawler.py`).
- Elasticsearch integration is wrapped in `ElasticService` (`app/services/es.py`); call `elastic_service` singleton rather than creating ad-hoc clients.
- WebSocket alerts go through `NotificationHub` (`app/services/notifications.py`) and `/api/ws/alerts` (`app/api/routes.py`).

## Project-Specific Conventions
- IDs are UUIDs at the DB/model level via `PrimaryIdMixin` (`app/db/base.py`), but many API responses stringify IDs explicitly (see `app/api/source/api.py`). Preserve this wire format.
- `source_type` and job `status` are stored as `IntEnum` values (`app/models/source_type.py`, `app/models/status.py`), not string enums.
- URL dedupe convention for crawlers is `select(Article).where(Article.url == ...)` before create (both HTML and RSS crawlers).
- Keyword matching uses boundary-aware regex in `detect_keywords()` (`app/services/keyword_detector.py`); normalize to lowercase with `normalize_keyword()`.
- Environment file selection is APP_MODE-driven (`app/core/env_settings.py`): `.env`, `.env-dev`, `.env-test`, `.env-prod`.

## Critical Workflows
- Install deps:
  - `pip install -r requirements.txt`
  - `pip install -r requirements-dev.txt`
- Run API locally (dev mode enables docs):
  - `$env:APP_MODE="dev"; uvicorn app.main:app --reload`
- Run tests (pytest config in `pyproject.toml`; tests use Postgres testcontainer + Alembic in `tests/conftest.py`):
  - `pytest`
- Run migrations:
  - `alembic upgrade head`
  - `alembic revision --autogenerate -m "<message>" --rev-id "<message>"`

## Integration Points To Respect
- PostgreSQL is required for runtime state and scheduler source definitions; scheduler reloads only `Source.is_enabled == True`.
- Elasticsearch index name is fixed as `articles` (`app/services/es.py`); search endpoint depends on this mapping.
- RSS parsing uses `feedparser`; HTML parsing uses BeautifulSoup+lxml; HTTP client is `httpx.AsyncClient`.
- Robots support exists (`app/services/robots.py`, `app/models/robots.py`) but is not yet wired into crawler execution paths.

## Safe Change Patterns
- When adding source/crawler behavior, update both scheduler switch mapping (`app/services/scheduler.py`) and crawler/scraper implementation.
- Keep API changes aligned with existing tests under `tests/source/*`, `tests/keywords/*`, and `tests/test_shealth_api.py`.
- Prefer placing new DB logic in existing service classes, not directly in route handlers.

