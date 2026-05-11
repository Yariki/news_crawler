from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status as HttpStatus

from app.api.keywords.services.keyword_service import KeywordService
from app.api.dependencies.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.keyword import MonitoredKeywordCreate, MonitoredKeywordRead, MonitoredKeywordUpdate

router = APIRouter(
    prefix="/keywords",
    tags=["keywords"],
)


@router.get("")
async def get_keywords(db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    words = await KeywordService(db).list_keywords(current_user.id)
    return [
        {
            "id": _.id,
            "keyword": _.keyword,
            "is_enabled": _.is_enabled
        } for _ in words
    ]


@router.get("/active")
async def get_active_keywords(db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    keywords = await KeywordService(db).get_active_keywords(current_user.id)
    return keywords


@router.get("/{keyword_id}")
async def get_keyword(keyword_id: UUID4, db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    word = await KeywordService(db).get_keyword(keyword_id, current_user.id)
    return {
        "id": word.id,
        "keyword": word.keyword,
        "is_enabled": word.is_enabled
    }


@router.post("", status_code=HttpStatus.HTTP_201_CREATED)
async def create_keyword(
    request: MonitoredKeywordCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    word = await KeywordService(db).create_keyword(request.keyword, current_user.id)
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
    current_user: CurrentUser = Depends(get_current_user),
):
    word = await KeywordService(db).update_keyword(keyword_id, current_user.id, request)
    return {
        "id": word.id,
        "keyword": word.keyword,
        "is_enabled": word.is_enabled
    }
