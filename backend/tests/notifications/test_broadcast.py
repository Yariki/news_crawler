import json
from uuid import uuid4

from app.services.notifications import NotificationHub


class FakeWebSocket:
    def __init__(self, fail_on_send: bool = False) -> None:
        self.fail_on_send = fail_on_send
        self.sent: list[str] = []
        self.closed = False

    async def send_text(self, data: str) -> None:
        if self.fail_on_send:
            raise RuntimeError("socket is gone")
        self.sent.append(data)

    async def close(self, code: int = 1000) -> None:
        self.closed = True


async def test_broadcast_sends_message_only_to_owner():
    hub = NotificationHub()
    owner_id, other_id = uuid4(), uuid4()
    owner_ws, other_ws = FakeWebSocket(), FakeWebSocket()
    hub._connections = {owner_id: owner_ws, other_id: other_ws}

    await hub.broadcast("KEYWORD_ALERT", {"owner_id": str(owner_id), "title": "hello"})

    assert len(owner_ws.sent) == 1
    assert json.loads(owner_ws.sent[0]) == {
        "type": "KEYWORD_ALERT",
        "payload": {"owner_id": str(owner_id), "title": "hello"},
    }
    assert other_ws.sent == []


async def test_broadcast_disconnects_failing_socket():
    hub = NotificationHub()
    owner_id, other_id = uuid4(), uuid4()
    failing_ws, other_ws = FakeWebSocket(fail_on_send=True), FakeWebSocket()
    hub._connections = {owner_id: failing_ws, other_id: other_ws}

    await hub.broadcast("KEYWORD_ALERT", {"owner_id": str(owner_id)})

    assert failing_ws.closed
    assert hub._connections == {other_id: other_ws}
    assert not other_ws.closed
