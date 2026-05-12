from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status as HttpStatus

from app.api.deps.auth import require_non_forced_password_change, require_permission
from app.core.rbac import Permission
from app.api.keywords.services.keyword_service import KeywordService
from app.db.session import get_db
from app.models.user import User
from app.schemas.keyword import MonitoredKeywordCreate, MonitoredKeywordUpdate

router = APIRouter(
    prefix="/keywords",
    tags=["keywords"],
)


@router.get("")
async def get_keywords(
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.KEYWORD_READ)),
):
    words = await KeywordService(db).list_keywords(actor=actor)
    return [
        {
            "id": _.id,
            "keyword": _.keyword,
            "is_enabled": _.is_enabled
        } for _ in words
    ]


@router.get("/active")
async def get_active_keywords(
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.KEYWORD_READ)),
):
    keywords = await KeywordService(db).get_active_keywords(actor=actor)
    return keywords


@router.get("/{keyword_id}")
async def get_keyword(
    keyword_id: UUID4,
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.KEYWORD_READ)),
):
    word = await KeywordService(db).get_keyword(keyword_id, actor=actor)
    return {
        "id": word.id,
        "keyword": word.keyword,
        "is_enabled": word.is_enabled
    }


@router.post("", status_code=HttpStatus.HTTP_201_CREATED)
async def create_keyword(
    request: MonitoredKeywordCreate,
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.KEYWORD_CREATE)),
    _: User | None = Depends(require_non_forced_password_change()),
):
    word = await KeywordService(db).create_keyword(request.keyword, actor=actor)
    return {
        "id": word.id,
        "keyword": word.keyword,
        "is_enabled": word.is_enabled
    }

@router.put("/{keyword_id}", status_code=HttpStatus.HTTP_200_OK)
async def update_keyword(
    keyword_id: UUID4, 
    request: MonitoredKeywordUpdate, 
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.KEYWORD_UPDATE)),
    _: User | None = Depends(require_non_forced_password_change()),
):
    word = await KeywordService(db).update_keyword(keyword_id, request, actor=actor)
    return {
        "id": word.id,
        "keyword": word.keyword,
        "is_enabled": word.is_enabled
    }


@router.delete("/{keyword_id}", status_code=HttpStatus.HTTP_204_NO_CONTENT)
async def delete_keyword(
    keyword_id: UUID4,
    db: AsyncSession = Depends(get_db),
    actor: User | None = Depends(require_permission(Permission.KEYWORD_DELETE)),
    _: User | None = Depends(require_non_forced_password_change()),
):
    await KeywordService(db).delete_keyword(keyword_id, actor=actor)
