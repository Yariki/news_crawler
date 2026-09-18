

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.core.rbac import PermissionMode, RequiredPermissionsAndOwnership
from app.services.notifications import notification_hub

router = APIRouter(prefix="/ws")


@router.websocket("/alerts")
async def alerts_ws(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts."""
    await notification_hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Since we no longer have the user_id here, we need to handle disconnection differently.
        # One approach is to modify the NotificationHub to track connections by websocket as well.
        # For now, we'll just close the websocket.
        await websocket.close()