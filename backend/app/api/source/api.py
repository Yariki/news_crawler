from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.source.services.source_service import SourceService
from app.db.session import get_db
from app.schemas.source import SourceCreate

router = APIRouter(
    prefix="source"
)

@router.get("")
async def get_source_list(
    db: AsyncSession = Depends(get_db)
):
    result = SourceService(db).list_sources();
    return result

@router.get("/{source_id}")
async def get_source(source_id: UUID4, 
                     db: AsyncSession = Depends(get_db)):
    result = SourceService(db).get_source(source_id)
    return result

@router.post("")
async def create_source(data: SourceCreate,
                        db: AsyncSession = Depends(get_db)):
    result = SourceService(db).create_source(data)
    return result



