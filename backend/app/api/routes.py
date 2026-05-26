from __future__ import annotations

from fastapi import APIRouter

from app.api.keywords.api import router as keywords_router
from app.api.source.api import router as source_router
from app.api.dashboard.api import router as dashboard_router
from app.api.messages.api import router as messages_router
from app.api.health.api import route as health_router
from app.api.articles.api import router as articles_router
from app.api.ws.api import router as ws_router

from app.core.config import settings

router = APIRouter(prefix="/api")

router.include_router(keywords_router)
router.include_router(source_router)
router.include_router(dashboard_router)
router.include_router(health_router)
router.include_router(articles_router)
router.include_router(ws_router)

if settings.app_mode == 'dev':
    router.include_router(messages_router)
