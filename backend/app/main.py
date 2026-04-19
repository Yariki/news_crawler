from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.services.es import elastic_service
from app.services.scheduler import refresh_scheduler_jobs, scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    await elastic_service.ensure_index()
    await refresh_scheduler_jobs()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.app_mode != "prod" else None,
    redoc_url="/redoc" if settings.app_mode != "prod" else None,
    openapi_url="/openapi.json" if settings.app_mode != "prod" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
