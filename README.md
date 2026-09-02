# Scraper

Full-stack project for collecting articles from different sources.

## Updated changes

- SQLAlchemy is now configured with the async provider (`AsyncEngine` + `AsyncSession`)
- FastAPI routes and crawl service now use async DB access
- Scheduler was moved to `AsyncIOScheduler`
- Alert keywords are no longer attached to a specific source
- Keywords are stored globally in `monitored_keywords` and can be managed from the dashboard

## Stack

- Backend: Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, APScheduler, Elasticsearch
- Frontend: Vue 3, TypeScript, Vuetify, Pinia, Vue Router, Axios
- Infra: Docker Compose


## Run with Docker

```bash
docker compose up --build
```

Services:

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- Elasticsearch: http://localhost:9200
- Postgres: localhost:5432

## Backend local run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
cp .env.example .env-dev
APP_MODE=dev alembic upgrade head
APP_MODE=dev uvicorn app.main:app --reload
```

## Auth

The app uses JWT access tokens, rotating refresh tokens, role-based access control, and row ownership. Start with these docs:

- [Permission matrix](docs/permission-matrix.md)
- [Auth architecture](docs/auth-architecture.md)
- [Admin guide](docs/admin-guide.md)
- [Migration notes](CHANGELOG.md#auth-migration-notes)

### JWT Flow

```mermaid
sequenceDiagram
    participant UI as Vue frontend
    participant API as FastAPI backend
    participant DB as PostgreSQL

    UI->>API: POST /api/auth/login (email, password)
    API->>DB: Load user, roles, permissions
    API->>DB: Store refresh token jti as ACTIVE
    API-->>UI: access_token + refresh_token
    UI->>API: Request with Authorization bearer access_token
    API->>API: Decode JWT and load current user
    API->>DB: Load AuthorizationContext
    API-->>UI: Protected response
    API-->>UI: 401 when access token expires
    UI->>API: POST /api/auth/refresh
    API->>DB: Rotate refresh token
    API-->>UI: New access_token + refresh_token
```

The frontend retries non-auth requests once after a successful refresh. Because refresh tokens rotate, concurrent refresh attempts are collapsed into a single in-flight request.

### Local Setup

Core backend env vars live in `backend/.env.example`:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/news_monitor
ELASTICSEARCH_URL=http://elasticsearch:9200
CORS_ORIGINS=http://localhost:5173
DEFAULT_KEYWORDS=
```

Auth-related settings have development defaults in `backend/app/core/config.py`, but set them explicitly for shared environments:

```bash
SECURITY_KEY=change-me
ALGORITHM=HS256
ACCESS_TTL_MINUTES=660
REFRESH_TTL_MINUTES=10080
ISSUER=News Crawler
```

`SECURITY_KEY` must be a real secret outside local development.

When `APP_MODE` is not `prod`, seed data is created during app startup through `app.db.seed_data.seed_data()`. The default local admin credentials are:

- Email/login username: `admin@user.com`
- Username: `admin`
- Password: `Admin123!`

The seeded `admin` role bypasses permission checks. The seeded `manager` and `user` roles start without permissions, and new registrations do not receive a role automatically, so assign roles from `/admin/users`.

For an existing database, run seeding before applying the owner backfill migration because existing rows are assigned to the seeded `admin` user:

```bash
cd backend
alembic upgrade head
```

### Add A New Permission

Permissions are named `resource:action:scope`; examples: `source:read:own`, `article:read:any`. Resources, actions, and scopes are validated in `backend/app/core/permission_types.py`, and the admin UI list is backed by `frontend/src/stores/admin.ts`.

To add a new permission category:

1. Add or confirm the resource/action/scope enum values in `backend/app/core/permission_types.py`.
2. Add the resource/action pair to `backend/app/services/resource_actions/resource_actions.py` so the catalog exposes it.
3. Protect the route with `RequiredPermissionsAndOwnership("resource:action:scope", mode=PermissionMode.ANY, resource_type=...)` when ownership checks are needed.
4. Use `filter_owned_resources()` or equivalent repository filtering for list/search reads.
5. Add tests for allowed, forbidden, and owner-mismatch cases.
6. Create or assign the permission from `/admin/roles`.

## Frontend local run

```bash
cd frontend
npm install
npm run dev
```

## Kubernetes and AKS

Helm chart: `k8s/news-crawler`

The chart deploys:

- frontend
- backend
- PostgreSQL
- Elasticsearch
- optional Kibana

Important deployment note:

- keep `backend.replicaCount=1` unless you split the scheduler out of the API process, because APScheduler starts inside the backend application lifecycle and would run once per replica

Render locally:

```bash
helm template news-crawler ./k8s/news-crawler
```

AKS workflow:

- GitHub Actions workflow: `.github/workflows/deploy-aks.yml`
- required repository variable placeholders: `AZURE_RESOURCE_GROUP`, `AZURE_AKS_CLUSTER_NAME`, `AZURE_CONTAINER_REGISTRY`, `AKS_INGRESS_HOST`
- required repository secret placeholders: `AZURE_CREDENTIALS`, `POSTGRES_PASSWORD`

## Notes about the scraper

This initial version uses straightforward HTML parsing:

- the homepage is crawled to discover article links
- article pages are parsed for title, date, body, author, and tags when available
- duplicate articles are avoided by `source_id + external_id` and `url`

The parser is intentionally heuristic so you can adapt it quickly if the site layout changes.
