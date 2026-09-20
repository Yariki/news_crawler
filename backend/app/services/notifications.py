from __future__ import annotations

import json
from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select

from app.core.config import settings
from app.core.rbac import RequiredPermissionsAndOwnership, PermissionMode
from app.db.session import  AsyncSession
from app.core.security import decode_token

from fastapi import WebSocket, status

import logging

from app.models import User

logger = logging.getLogger(__name__)

class NotificationHub:
    def __init__(self) -> None:
        self._connections: dict[UUID, WebSocket] = {}

    async def connect(self, websocket: WebSocket, db: AsyncSession) -> None:
        
        try:
            await websocket.accept()
            logger.info("Accepting websocket connection...")
            user_token = await websocket.receive_json()
            decoded_token = decode_token(user_token.get("token"), settings)

            if not decoded_token:
                logger.warning("Invalid token")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            is_valid_user = await self._validate_user(decoded_token, db)
            if not is_valid_user:
                logger.warning("User validation failed")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            user_id = UUID(decoded_token.get("sub"))
            logger.info(f"User {user_id} connected successfully.")
            
            await websocket.send_text(json.dumps({"type": "CONNECTION_SUCCESSFUL", "payload": {"user_id": str(user_id)}}))
            
            self._connections[user_id] = websocket
            logger.info(f"Current connections: {list(self._connections.keys())}")
        except Exception as e:
            logger.error(f"Failed to accept websocket connection: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    async def disconnect(self, web_socket: WebSocket) -> None:
        user_id = None
        for uid, ws in self._connections.items():
            if ws == web_socket:
                user_id = uid
                break
        if user_id:
            await self._connections[user_id].close()
            del self._connections[user_id]

    async def broadcast(self, event_type: str, payload: dict) -> None:
        dead: list[UUID] = []
        owner_id= UUID(payload.get("owner_id", None)) if payload.get("owner_id", None) else None
        if not owner_id:
            logger.warning("Invalid payload. There is no owner_id in the payload.")
            return
        message = json.dumps({"type": event_type, "payload": payload}, ensure_ascii=False)
        for user_id, connection in list(self._connections.items()):
            try:
                if owner_id and user_id == owner_id:
                    await connection.send_text(data=message)
            except Exception:
                dead.append(user_id)
        for user_id in dead:
            self.disconnect(user_id)
            
    async def _validate_user(self, decoded_token: dict[str, str], db: AsyncSession) -> bool:
        user_id = decoded_token.get("sub")
        if not user_id:
            logger.warning("Token does not contain user ID")
            return False

        query = select(User).where(User.id == user_id, User.is_active.is_(True))
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            logger.warning(f"User {user_id} not found or inactive")
            return False
        access_control = RequiredPermissionsAndOwnership("alert:read:own", mode=PermissionMode.ANY)
        try:

            granted = await access_control.check_permissions(db, user_id)
            if not granted:
                logger.warning(f"User {user_id} does not have permission to read alerts")
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking permissions for user {user_id}: {e}")
            return False

notification_hub = NotificationHub()
