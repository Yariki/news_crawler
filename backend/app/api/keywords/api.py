from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status as HttpStatus

from app.api.keywords.services.keyword_service import KeywordService
from app.api.source.services.source_service import SourceService
from app.db.session import get_db
from app.schemas.keyword import MonitoredKeywordCreate, MonitoredKeywordRead, MonitoredKeywordUpdate

router = APIRouter(
    prefix="/keywords",
    tags=["keywords"],
)


@router.get("")
async def get_keywords(db: AsyncSession = Depends(get_db)):
    words = await KeywordService(db).list_keywords()
    return [
        {
            "id": _.id,
            "keyword": _.keyword,
            "is_enabled": _.is_enabled
        } for _ in words
    ]


@router.get("/active")
async def get_active_keywords(db: AsyncSession = Depends(get_db)):
    keywords = await KeywordService(db).get_active_keywords()
    return keywords


@router.get("/{keyword_id}")
async def get_keyword(keyword_id: UUID4, db: AsyncSession = Depends(get_db)):
    word = await KeywordService(db).get_keyword(keyword_id)
    return {
        "id": word.id,
        "keyword": word.keyword,
        "is_enabled": word.is_enabled
    }


@router.post("", status_code=HttpStatus.HTTP_201_CREATED)
async def create_keyword(
    request: MonitoredKeywordCreate, db: AsyncSession = Depends(get_db)
):
    word = await KeywordService(db).create_keyword(request.keyword)
    return {
        "id": word.id,
        "keyword": word.keyword,
        "is_enabled": word.is_enabled
    }

@router.put("/{keyword_id}", status_code=HttpStatus.HTTP_200_OK)
async def update_keyword(
    keyword_id: UUID4, 
    request: MonitoredKeywordUpdate, 
    db: AsyncSession = Depends(get_db)
):
    word = await KeywordService(db).update_keyword(keyword_id, request)
    return {
        "id": word.id,
        "keyword": word.keyword,
        "is_enabled": word.is_enabled
    }
