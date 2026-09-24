from fastapi import APIRouter, Depends, Response, status
from app.core.rbac import RequiredPermissionsAndOwnership, PermissionMode
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.responses import StreamingResponse
import io

from app.services.backup.export_sources import export_sources
from app.db.session import get_db

router = APIRouter(prefix="/backup", tags=["backup"])

@router.get("/sources/download", response_model=None)
async def backup_sources(db: AsyncSession = Depends(get_db), \
                        access_control=Depends(RequiredPermissionsAndOwnership("source:read:own", mode=PermissionMode.ANY))):

    try:
        data =  await export_sources(db, access_control.auth.user_id, access_control)
        return StreamingResponse(
                io.BytesIO(data), 
                media_type="application/json",
                headers={"Content-Disposition": 'attachment; filename="sources.json"'}
            )
        
    except Exception as e:
        return Response(
            content="Error occured during backup sources",
            media_type="application/text; charset=utf-8",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    