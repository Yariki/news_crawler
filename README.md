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
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Frontend local run

```bash
cd frontend
npm install
npm run dev
```

## Notes about the scraper

This initial version uses straightforward HTML parsing:

- the homepage is crawled to discover article links
- article pages are parsed for title, date, body, author, and tags when available
- duplicate articles are avoided by `source_id + external_id` and `url`

The parser is intentionally heuristic so you can adapt it quickly if the site layout changes.
