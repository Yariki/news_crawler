from __future__ import annotations

import json
from collections.abc import Iterable
from uuid import UUID
from app.core.config import settings
from app.core.rbac import RequiredPermissionsAndOwnership, PermissionMode
from app.db.session import DbSession, get_db
from app.core.security import decode_token

from fastapi import WebSocket, status

import logging

logger = logging.getLogger(__name__)

class NotificationHub:
    def __init__(self) -> None:
        self._connections: dict[UUID, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> None:
        
        try:
            await websocket.accept()
            logger.info("Accepting websocket connection...")
            user_token = await websocket.receive_json()
            decoded_token = decode_token(user_token.get("token"), settings)
            
            access_control = RequiredPermissionsAndOwnership("alert:read:own", mode=PermissionMode.ANY)
            
            
            if not decoded_token:
                logger.warning("Invalid token")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            
            user_id = UUID(decoded_token.get("sub"))
            logger.info(f"User {user_id} connected successfully.")
            
            await websocket.send_text(json.dumps({"type": "CONNECTION_SUCCESSFUL", "payload": {"user_id": str(user_id)}}))
            
            self._connections[user_id] = websocket
            logger.info(f"Current connections: {list(self._connections.keys())}")
        except Exception as e:
            logger.error(f"Failed to accept websocket connection: {e}")
            return

    def disconnect(self, user_id: UUID) -> None:
        if user_id in self._connections:
            del self._connections[user_id]

    async def broadcast(self, event_type: str, payload: dict) -> None:
        dead: list[UUID] = []
        owner_id= UUID(payload.get("owner_id"))
        message = json.dumps({"type": event_type, "payload": payload}, ensure_ascii=False)
        for user_id, connection in list(self._connections.items()):
            try:
                if owner_id and user_id == owner_id:
                    await connection.send_text(data=message)
            except Exception:
                dead.append(user_id)
        for user_id in dead:
            self.disconnect(user_id)
            
    async def _validate_user(self, token: str) -> bool:
        # TODO: implement validation of the user token
        pass


notification_hub = NotificationHub()
