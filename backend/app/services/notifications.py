from __future__ import annotations

import json
from collections.abc import Iterable

from fastapi import WebSocket


class NotificationHub:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, event_type: str, payload: dict) -> None:
        dead: list[WebSocket] = []
        message = json.dumps({"type": event_type, "payload": payload}, ensure_ascii=False)
        for connection in list(self._connections):
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.disconnect(connection)


notification_hub = NotificationHub()
