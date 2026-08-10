
from fastapi import APIRouter, Depends
from app.core.rbac import OwnedResourceType
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status as HttpStatus, HTTPException

from app.core.auth import CurrentActiveUser, CurrentUser
from app.core.rbac import PermissionMode, RequiredPermissionsAndOwnership
from app.repositories.monitore_keyword_repository import MonitoreKeywordRepository

from app.db.session import get_db
from app.schemas.keyword import MonitoredKeywordCreate, MonitoredKeywordRead, MonitoredKeywordUpdate

router = APIRouter(
    prefix="/keywords",
    tags=["keywords"],
)


@router.get("", response_model=list[MonitoredKeywordRead])
async def get_keywords(current_user: CurrentActiveUser, db: AsyncSession = Depends(get_db), access_control=Depends(RequiredPermissionsAndOwnership("keyword:read:own", mode=PermissionMode.ANY))):
    words = await MonitoreKeywordRepository(db, access_control).list_keywords(current_user.id)
    return words


@router.get("/active", response_model=list[str])
async def get_active_keywords(db: AsyncSession = Depends(get_db), access_control=Depends(RequiredPermissionsAndOwnership("keyword:read:own", mode=PermissionMode.ANY))):
    keywords = await MonitoreKeywordRepository(db, access_control).get_active_keywords()
    return keywords


@router.get("/{resource_id}", response_model=MonitoredKeywordRead)
async def get_keyword(resource_id: UUID4, db: AsyncSession = Depends(get_db), access_control=Depends(RequiredPermissionsAndOwnership("keyword:read:own", mode=PermissionMode.ANY, resource_type=OwnedResourceType.MONITORED_KEYWORD))):
    word = await MonitoreKeywordRepository(db, access_control).get_keyword(resource_id)
    return word


@router.post("", status_code=HttpStatus.HTTP_201_CREATED, response_model=MonitoredKeywordRead)
async def create_keyword(
    request: MonitoredKeywordCreate, db: AsyncSession = Depends(get_db), access_control=Depends(RequiredPermissionsAndOwnership("keyword:create:own", mode=PermissionMode.ANY))
):

    request.keyword = request.keyword.lower().strip()

    if len(request.keyword) == 0:
        raise HTTPException(status_code=HttpStatus.HTTP_400_BAD_REQUEST, detail="Keyword cannot be empty")

    word = await MonitoreKeywordRepository(db, access_control).create_keyword(request.keyword, access_control.auth.user_id)
    return word

@router.put("/{resource_id}", status_code=HttpStatus.HTTP_200_OK, response_model=MonitoredKeywordRead)
async def update_keyword(
    resource_id: UUID4,
    request: MonitoredKeywordUpdate,
    db: AsyncSession = Depends(get_db), access_control=Depends(RequiredPermissionsAndOwnership("keyword:update:own", mode=PermissionMode.ANY, resource_type=OwnedResourceType.MONITORED_KEYWORD))
):

    request.keyword = request.keyword.lower().strip()
    if len(request.keyword) == 0:
        raise HTTPException(status_code=HttpStatus.HTTP_400_BAD_REQUEST, detail="Keyword cannot be empty")

    word = await MonitoreKeywordRepository(db, access_control).update_keyword(resource_id, request)
    return word
