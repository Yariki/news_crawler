

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.core.rbac import PermissionMode, RequiredPermissionsAndOwnership
from app.services.notifications import notification_hub


router = APIRouter(prefix="/ws")


@router.websocket("/alerts")
async def alerts_ws(websocket: WebSocket, access_control=Depends(RequiredPermissionsAndOwnership("alert:read:own", mode=PermissionMode.ANY))):
    """WebSocket endpoint for real-time alerts."""
    await notification_hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_hub.disconnect(websocket)