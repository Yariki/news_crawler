from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from app.core.rbac import RequiredPermissionsAndOwnership, PermissionMode
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.responses import StreamingResponse
import io

from app.services.backup.export_sources import export_sources, import_sources
from app.db.session import get_db

router = APIRouter(prefix="/backup", tags=["backup"])

MAX_UPLOAD_BYTES = 1 * 1024 * 1024  # 1 MB

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

@router.post("/sources/upload", response_model=None)
async def upload_sources( file: UploadFile = (...),
                        db: AsyncSession = Depends(get_db), \
                        access_control=Depends(RequiredPermissionsAndOwnership("source:create:own", mode=PermissionMode.ANY))):
    
    if file.content_type not in ("application/json", "text/json", "application/octet-stream"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only JSON files are accepted")

    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is too large")

    return await import_sources(db, access_control.auth.user_id, access_control, raw)
    