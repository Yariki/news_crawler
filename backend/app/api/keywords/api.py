from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status as HttpStatus

from app.repositories.monitore_keyword_repository import MonitoreKeywordRepository

from app.db.session import get_db
from app.schemas.keyword import MonitoredKeywordCreate, MonitoredKeywordRead, MonitoredKeywordUpdate

router = APIRouter(
    prefix="/keywords",
    tags=["keywords"],
)


@router.get("", response_model=list[MonitoredKeywordRead])
async def get_keywords(db: AsyncSession = Depends(get_db)):
    words = await MonitoreKeywordRepository(db).list_keywords()
    return words


@router.get("/active", response_model=list[str])
async def get_active_keywords(db: AsyncSession = Depends(get_db)):
    keywords = await MonitoreKeywordRepository(db).get_active_keywords()
    return keywords


@router.get("/{keyword_id}", response_model=MonitoredKeywordRead)
async def get_keyword(keyword_id: UUID4, db: AsyncSession = Depends(get_db)):
    word = await MonitoreKeywordRepository(db).get_keyword(keyword_id)
    return word 


@router.post("", status_code=HttpStatus.HTTP_201_CREATED, response_model=MonitoredKeywordRead)
async def create_keyword(
    request: MonitoredKeywordCreate, db: AsyncSession = Depends(get_db)
):
    word = await MonitoreKeywordRepository(db).create_keyword(request.keyword)
    return word

@router.put("/{keyword_id}", status_code=HttpStatus.HTTP_200_OK, response_model=MonitoredKeywordRead)
async def update_keyword(
    keyword_id: UUID4, 
    request: MonitoredKeywordUpdate, 
    db: AsyncSession = Depends(get_db)
):
    word = await MonitoreKeywordRepository(db).update_keyword(keyword_id, request)
    return word
