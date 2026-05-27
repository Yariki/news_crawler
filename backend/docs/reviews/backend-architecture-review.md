# Backend Architecture And Code Review

Reviewed on: 2026-05-27

Scope: static review of the FastAPI backend architecture, API/service boundaries, crawlers, persistence models, integrations, and tests.

## Executive Summary

The project has a clear high-level shape: FastAPI exposes a thin API layer, SQLAlchemy models persist runtime state, APScheduler drives crawls, crawler services orchestrate scraping, PostgreSQL stores articles/jobs/keywords, Elasticsearch powers search, and WebSocket notifications broadcast keyword alerts.

The main architectural concern is that crawling currently mixes several responsibilities in one flow: database writes, duplicate detection, keyword hit creation, Elasticsearch indexing, WebSocket notification, robots handling, and job status updates. This makes failure modes harder to reason about and creates gaps where persisted data, search index state, and notifications can diverge.

The most important improvements are:

- Fix correctness bugs in robots caching and alert JSON serialization.
- Make article ingestion idempotent and reusable across HTML, RSS, and Telegram crawlers.
- Separate durable database writes from external side effects through an outbox or retryable indexing/notification mechanism.
- Revisit APScheduler deployment so crawls do not duplicate across multiple API workers.
- Add tests around crawler behavior and integration failure paths.

## Findings

### High Severity

1. Robots caching is fragile enough to break repeat crawls.

   `RobotSite` requires `can_fetch`, but `RobotRepository.get_robot_by_url()` does not provide it. Cached robot rows can raise `TypeError`. There is also a `datetime.now(...)` call after `import datetime`, which will raise `AttributeError`, and stale robot refresh inserts a duplicate `url` instead of updating the existing row.

   Files:

   - `app/dto/robot_site.py`
   - `app/repositories/robot_repository.py`
   - `app/services/robots.py`

2. Crawler writes, Elasticsearch indexing, and WebSocket alerts are not atomic or recoverable.

   HTML and RSS crawlers commit articles before indexing and notification. If Elasticsearch or WebSocket delivery fails, the DB row remains and future crawls skip it by URL, so it may never be indexed or alerted. Telegram does the inverse in places: it sends notifications and indexes before committing the article, so clients can see alerts for data that may not persist.

   Files:

   - `app/services/crawlers/html_crawler.py`
   - `app/services/crawlers/rss_crawler.py`
   - `app/services/crawlers/telegram_crawler.py`

3. WebSocket alert serialization can fail on real alerts.

   `_send_notification()` passes UUID and `datetime` objects into `json.dumps()`, which cannot serialize them by default. The payload should stringify IDs and use ISO timestamps before passing data to `NotificationHub`.

   Files:

   - `app/services/crawlers/base_crawler.py`
   - `app/services/notifications.py`

4. In-process APScheduler can duplicate crawls in production.

   App startup always starts the scheduler. With multiple Uvicorn workers or multiple deployed replicas, every process starts its own scheduler and runs the same source jobs.

   Files:

   - `app/main.py`
   - `app/services/scheduler.py`

### Medium Severity

5. HTTP clients are leaked.

   `BaseScraper`, `RssScraper`, and `RobotsService` create `httpx.AsyncClient` instances without closing them. Use `async with`, an explicit `aclose()`, or lifespan-scoped clients.

   Files:

   - `app/scrapers/base_scraper.py`
   - `app/scrapers/rss/rss_scraper.py`
   - `app/services/robots.py`

6. Scheduler state is not updated when sources are created.

   `create_source()` commits the new source, but new enabled sources are not scheduled until `refresh_scheduler_jobs()` runs again, likely after restart.

   Files:

   - `app/api/source/services/source_service.py`
   - `app/services/scheduler.py`

7. Models and schemas have inconsistent typing and validation.

   `CrawlJob.source_id` is annotated as `int` while the database FK is UUID. `SourceCreateUpdate.base_url: HttpUrl | str` accepts arbitrary strings, and `source_type` is an unconstrained `int`.

   Files:

   - `app/models/crawl_job.py`
   - `app/schemas/source.py`

8. API response shaping is duplicated and uneven.

   Source endpoints manually build almost identical dictionaries multiple times. Keyword and dashboard endpoints often omit `response_model`, so API contracts are less explicit and less consistently documented.

   Files:

   - `app/api/source/api.py`
   - `app/api/keywords/api.py`
   - `app/api/dashboard/api.py`

9. Test coverage is narrow compared with the system risk.

   Current tests cover basic health, source, and keyword flows. They do not cover crawler ingestion, robots behavior, WebSocket alert serialization, scheduler refresh, Elasticsearch failure, duplicate URL races, or app lifespan startup.

   Files:

   - `tests/conftest.py`
   - `tests/source/*`
   - `tests/keywords/*`

### Low Severity And Operational Concerns

10. Environment-specific files are tracked.

    `.env-dev`, `.env-test`, and `.env-prod` are tracked. Even if sanitized today, best practice is to track only `.env.example` and keep real environment files local or secret-managed.

11. Logging is inconsistent.

    Some paths still use `print()` for crawler discovery, bot challenge detection, and scheduler errors. Prefer structured logging with source IDs, URLs, and job IDs.

12. Naming and style cleanup would improve maintainability.

    Examples include `dashbord_service.py`, `TelegramScrapper`, unused imports, inconsistent route variable names, and inconsistent `route` vs `router` naming.

## Architecture Recommendations

### 1. Introduce A Shared Article Ingestion Service

Create a service responsible for converting a `ScrapedArticle` into durable database state:

- Normalize source and article IDs.
- Check duplicates.
- Create `Article`.
- Detect keywords.
- Create `KeywordHit` rows.
- Return a structured result describing whether the article was new, duplicate, alerting, or failed.

This would remove duplicated logic from HTML, RSS, and Telegram crawlers and make behavior consistent.

Suggested location:

- `app/services/article_ingestion.py`

### 2. Use An Outbox For External Side Effects

Database writes should be the source of truth. Elasticsearch indexing and WebSocket notifications should be retryable side effects.

Recommended pattern:

1. Crawler commits article and keyword hits.
2. Crawler creates outbox events such as `article.index_requested` and `keyword.alert_requested`.
3. A background worker processes outbox events.
4. Failed events are retried with error details and attempt counts.

This prevents silent gaps where articles exist in PostgreSQL but are missing from Elasticsearch or alert delivery.

### 3. Make Crawlers Idempotent And Race-Safe

The current URL dedupe query is useful but not sufficient under concurrency. Keep the unique URL constraint, and also handle `IntegrityError` or use Postgres `ON CONFLICT DO NOTHING`.

Add constraints and indexes:

- Unique `(source_id, external_id)` for source-native IDs.
- Unique `(article_id, keyword)` for keyword hits.
- Index `articles.source_id`.
- Index `articles.published_at`.
- Index `articles.is_alert`.
- Index `crawl_jobs.source_id`.

### 4. Separate Scheduler From API Runtime In Production

Options:

- Run the scheduler as a single separate process.
- Use a distributed lock or leader-election mechanism.
- Replace in-process scheduling with a durable task queue.

At minimum, guard scheduler startup by configuration so it can be disabled for API-only workers.

### 5. Tighten API Contracts

Recommended changes:

- Add `response_model` to every route.
- Use Pydantic serializers instead of repeated manual dict shaping.
- Keep UUIDs stringified where required by the existing wire format.
- Validate `scrape_interval_minutes` with a positive lower bound.
- Validate `source_type` against `SourceType`.
- Use separate create and update schemas if update behavior diverges.

### 6. Improve Resource Management

Use one of these patterns for HTTP clients:

- `async with httpx.AsyncClient(...) as client`
- scraper-level `close()` called from crawler `finally`
- app-lifespan shared client injected into services

Also consider consistent request timeouts, retry policy, user agent, and backoff.

### 7. Improve Observability

Add structured logs for:

- Crawl start and finish.
- Source ID, job ID, crawler type.
- Article discovered, skipped, created, indexed.
- Robots blocked URLs.
- External service failures.

Add dashboard-level visibility for:

- Last successful crawl per source.
- Last failed crawl per source.
- Indexing backlog or failed outbox events.

## Testing Recommendations

Add focused tests for the highest-risk paths:

- Robots service first fetch, cached fetch, stale refresh, missing robots response.
- Notification payload JSON encoding for UUID and datetime.
- HTML/RSS crawler happy path with mocked scraper and Elasticsearch.
- Crawler behavior when Elasticsearch fails after DB commit.
- Duplicate URL handling under unique constraint.
- Scheduler refresh after source creation or source enablement.
- Telegram crawler incremental `last_message_id` behavior.
- Source schema validation for invalid URL, invalid source type, and non-positive scrape interval.

## Suggested Implementation Order

1. Fix robots service and notification serialization bugs.
2. Close HTTP clients correctly.
3. Add tests around those fixes.
4. Extract shared article ingestion logic.
5. Add idempotency constraints and duplicate-race handling.
6. Add outbox/retry for Elasticsearch and WebSocket side effects.
7. Make scheduler deployment explicit and configurable.
8. Tighten API schemas and response models.

## Notes

This review was static. The test suite was not run because it uses Testcontainers/Postgres and the task was an architecture/code review rather than a verification pass.
