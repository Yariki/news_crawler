from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.keywords.services.keyword_service import KeywordService
from app.api.source.services.source_service import SourceService
from app.db.session import get_db

router = APIRouter(
    prefix="/keywords",
)

@router.get("")
async def get_keywords(db: AsyncSession = Depends(get_db)):
    words = KeywordService(db).list_keywords()
    return words

@router.get("/active")
async def get_active_keywords(db: AsyncSession = Depends(get_db)):
    keywords = KeywordService(db).get_active_keywords()
    return keywords

@router.get("/{keyword_id}")
async def get_keyword(keyword_id: UUID4, db: AsyncSession = Depends(get_db)):
    word = KeywordService(db).get_keyword(keyword_id)
    return word

@router.post("")
async def create_keyword(keyword: str, db: AsyncSession = Depends(get_db)):
    word = KeywordService(db).create_keyword(keyword)
    return word