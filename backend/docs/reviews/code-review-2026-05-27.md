# Code Review — Backend

**Date:** 2026-05-27  
**Reviewer:** Claude (automated static analysis)  
**Scope:** Architecture, code quality, bugs, security, data model — full backend scan

---

## Executive Summary

The overall structure is solid — clean layering, async throughout, good use of FastAPI patterns. However there are several concrete bugs, significant code duplication, and architectural gaps worth addressing. Findings are grouped by severity.

---

## Bugs (Fix These First)

### 1. `robots.py` — datetime import causes runtime crash

**File:** `app/services/robots.py:84`

```python
# top of file: `import datetime`  (the module, not the class)
period = datetime.now(datetime.timezone.utc)  # AttributeError: module has no attr 'now'
```

`datetime` resolves to the module here, not `datetime.datetime`. This crashes `_check_and_update_robot` on every call, meaning the 7-day refresh of cached robots.txt content never executes.

**Fix:**
```python
from datetime import datetime, timezone
period = datetime.now(timezone.utc) - robot_site.updated_at
```

---

### 2. `BaseScraper` — `httpx.AsyncClient` is never closed

**Files:** `app/scrapers/base_scraper.py:21`, `app/services/robots.py:57`

The `httpx.AsyncClient` is instantiated in `__init__` and in `_load_robot()` but `aclose()` is never called. This leaks a connection pool on every crawl cycle.

**Fix for `BaseScraper`:** Use as an async context manager per request, or add `__aenter__`/`__aexit__`:
```python
async with httpx.AsyncClient(...) as client:
    response = await client.get(url)
```

**Fix for `RobotsService._load_robot()`:** Same — wrap the client in `async with`.

---

### 3. `base_scraper.py` — Debug `print()` left in production code

**File:** `app/scrapers/base_scraper.py:40`

```python
print(f"Discovered URL: {full_url}; {any(...)}")
```

Replace with `logger.debug(...)`.

---

### 4. `scheduler.py` — `print()` instead of structured logging

**File:** `app/services/scheduler.py:73`

```python
print(f"Error running scheduled job for source {source_id}: {e}")
```

Replace with `logger.error(...)` so it flows through the configured logging pipeline.

---

## Architecture Issues

### 5. Massive duplication between `HtmlCrawlService` and `RssCrawlService`

**Files:** `app/services/crawlers/html_crawler.py`, `app/services/crawlers/rss_crawler.py`

Both crawlers share ~80% of the same logic: job creation, error handling, keyword detection, article construction, Elasticsearch indexing, and WebSocket notifications. `BaseCrawler` exists but is barely used beyond `_get_keywords`, `_index_article`, and `_send_notification`.

**Recommendation:** Extract a template method `_run_crawl_loop()` into `BaseCrawler`:

```python
# BaseCrawler
async def _save_article(self, source, scraped, active_keywords) -> Article | None:
    """Dedup-check, construct, persist, index, notify. Returns None if skipped."""
    ...

async def _create_job(self, source_id) -> CrawlJob:
    ...

async def _finish_job(self, job, created, exc=None) -> None:
    ...
```

This eliminates ~120 lines of duplicated code and ensures consistent error handling and job lifecycle across all crawler types.

---

### 6. Inconsistent repository pattern

`RobotRepository` uses the repository pattern, but all other database access is done inline in services and endpoint handlers (e.g., `html_crawler.py:55`, `articles/api.py:17`, `dashboard/services/`). Pick one approach and apply it consistently — either introduce `ArticleRepository`, `SourceRepository`, etc., or drop `RobotRepository` and access the DB directly everywhere.

---

### 7. Manual dict serialization in API route handlers

**File:** `app/api/source/api.py:18-58`

Every handler manually constructs a response dict:
```python
return {
    "id": str(_.id),
    "name": _.name,
    ...
}
```

Since `SourceRead` is already configured with `model_config = ConfigDict(from_attributes=True)`, FastAPI can serialize ORM objects directly:
```python
return await SourceService(db).list_sources()
```

The same pattern repeats in keyword and dashboard endpoints.

---

### 8. N+1 query in crawl loop

**Files:** `app/services/crawlers/html_crawler.py:55`, `app/services/crawlers/rss_crawler.py:53`

For each of N discovered URLs, a separate `SELECT` checks for duplicates:
```python
for url in urls:
    existing = await self.db.scalar(select(Article).where(Article.url == url))
```

On a site with 100 links this is 100 round-trips. Batch it before the loop:
```python
existing_urls = set(await self.db.scalars(
    select(Article.url).where(Article.url.in_(urls))
))
for url in urls:
    if url in existing_urls:
        continue
```

---

### 9. Circular import workaround via lazy imports

**File:** `app/services/crawlers/base_crawler.py:31,47`

```python
async def _index_article(self, ...):
    from app.services.es import elastic_service      # lazy import
async def _send_notification(self, ...):
    from app.services.notifications import notification_hub  # lazy import
```

Lazy imports indicate a circular dependency caused by module-level singletons (`elastic_service`, `notification_hub`). The fix is to inject these as constructor arguments to `BaseCrawler`:

```python
class BaseCrawler(ABC):
    def __init__(self, db: AsyncSession, es=None, hub=None):
        self.db = db
        self.es = es or elastic_service
        self.hub = hub or notification_hub
```

This also makes the crawlers properly testable without patching imports.

---

### 10. Language hardcoded to `"ru"`

**File:** `app/scrapers/base_scraper.py:79`

```python
language="ru",  # hardcoded
```

`Source` already has a `language` field. Pass it through the scraper constructor and use it here.

---

### 11. Three near-identical scheduler wrapper functions

**File:** `app/services/scheduler.py:19-34`

```python
async def _run_source_job(source_id): ...
async def _run_rss_job(source_id): ...
async def _run_telegram_job(source_id): ...
```

These differ only in which service class is instantiated. Collapse into one generic function:
```python
async def _run_job(source_id: str, service_cls: type[BaseCrawler]) -> None:
    async with AsyncSessionLocal() as db:
        await service_cls(db).crawl(source_id)

switcher = {
    SourceType.NEWS_SITE: partial(_run_job, service_cls=HtmlCrawlService),
    SourceType.RSS:        partial(_run_job, service_cls=RssCrawlService),
    SourceType.TELEGRAM_CHANNEL: partial(_run_job, service_cls=TelegramCrawlerService),
}
```

---

## Data Model Issues

### 12. `tags_csv` and `matched_keywords_csv` stored as CSV strings

**File:** `app/models/article.py:30`

Storing arrays as comma-separated strings loses queryability. Filtering articles by tag requires `LIKE '%tag%'` — slow and error-prone. PostgreSQL supports `ARRAY(String)` natively:
```python
from sqlalchemy.dialects.postgresql import ARRAY
tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
```

Alternatively, a separate `article_tags` join table for full relational integrity.

---

### 13. No unique constraint on `(source_id, external_id)`

**File:** `app/models/article.py`

`url` is unique, but `external_id` has no constraint. If the same article is reachable via different URL forms, duplicate content can slip through. Add:
```python
__table_args__ = (UniqueConstraint("source_id", "external_id"),)
```

---

### 14. APScheduler job state is in-memory only

On app restart, all scheduled jobs reset their next-run times — every source crawls immediately at startup. For production, persist job state using APScheduler's built-in job store:
```python
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
jobstores = {"default": SQLAlchemyJobStore(url=settings.alembic_database_url)}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")
```

---

## Security Gaps

### 15. No authentication on any endpoint

All API endpoints are fully open — `/sources`, `/keywords`, and especially `/messages` (test broadcast). At minimum, add a static API key check via FastAPI dependency:
```python
async def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=403)
```

---

### 16. No input validation on search endpoint

**File:** `app/api/articles/api.py:21`

`q` is passed directly to Elasticsearch with no length limit:
```python
async def search_articles(q: str):
```

Add constraints:
```python
async def search_articles(q: str = Query(..., min_length=1, max_length=200)):
```

---

### 17. Telegram session file is not configurable

**File:** `app/scrapers/telegram/telegram_scraper.py`

The Telethon session file is written to the working directory. In a Docker container this is lost on restart. The path should be configurable via `settings.telegram_session_path`.

---

## Operational Issues

### 18. No pagination on list endpoints

`GET /sources`, `GET /keywords`, and `GET /articles/recent` lack proper pagination. As articles accumulate, unbounded queries will degrade. Add `offset`/`limit` (or cursor-based) pagination:
```python
async def get_recent_articles(limit: int = Query(20, le=100), offset: int = 0, ...):
```

---

### 19. `finished_at` set redundantly in `html_crawler.py`

**File:** `app/services/crawlers/html_crawler.py:109,131`

`job.finished_at` is set in the `try` block (line 109) and again in `finally` (line 131). The `finally` write always overwrites the `try` write — keep it only in `finally`.

---

## Minor Code Quality

| File | Line | Issue |
|---|---|---|
| `app/api/dashboard/services/dashbord_service.py` | filename | Typo: `dashbord` → `dashboard` |
| `app/services/crawlers/base_crawler.py` | 16 | Multi-paragraph docstring on abstract method — the signature is self-documenting |
| `app/core/config.py` | 41-46 | `lru_cache` is fine but the module-level `settings = get_settings()` makes test overrides require patching the import rather than the function; use `Depends(get_settings)` in handlers instead |
| All crawlers | — | `job.articles_found` is set after `commit()` but never committed on its own; it's only persisted via the `finally` block — this is fine but non-obvious |

---

## Priority Order

| # | Issue | Impact |
|---|---|---|
| 1 | `robots.py` datetime bug | Silent crash on every non-first crawl |
| 2 | `httpx` client leak | Resource leak on every crawl cycle |
| 3 | Remove `print()` statements | Noise in production logs |
| 4 | Deduplicate crawl loop into `BaseCrawler` | Biggest maintenance burden |
| 5 | N+1 query fix in crawl loop | Performance at scale |
| 6 | Add API authentication | Security gap |
| 7 | Replace CSV columns with array types | Data model correctness |
| 8 | Pagination on list endpoints | Operational stability |
