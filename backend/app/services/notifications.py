from __future__ import annotations

import json
from collections.abc import Iterable
from uuid import UUID

from fastapi import WebSocket


class NotificationHub:
    def __init__(self) -> None:
        self._connections: dict[UUID, WebSocket] = {}

    async def connect(self, user_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id] = websocket

    def disconnect(self, user_id: UUID) -> None:
        if user_id in self._connections:
            del self._connections[user_id]

    async def broadcast(self, event_type: str, payload: dict) -> None:
        dead: list[WebSocket] = []
        message = json.dumps({"type": event_type, "payload": payload}, ensure_ascii=False)
        for user_id, connection in list(self._connections.items()):
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(user_id)
        for user_id in dead:
            self.disconnect(user_id)


notification_hub = NotificationHub()
