from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock

from fastapi import HTTPException, Request, status

from app.core.config import settings


class AuthRateLimiter:
    def __init__(self) -> None:
        self._bucket: dict[str, deque[datetime]] = defaultdict(deque)
        self._failed_logins: dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def check(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=1)
        with self._lock:
            queue = self._bucket[client_ip]
            while queue and queue[0] < window_start:
                queue.popleft()
            if len(queue) >= settings.auth_rate_limit_per_minute:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many auth requests")
            queue.append(now)

    def register_login_result(self, request: Request, success: bool) -> None:
        client_ip = request.client.host if request.client else "unknown"
        with self._lock:
            if success:
                self._failed_logins.pop(client_ip, None)
                return
            self._failed_logins[client_ip] += 1

    def abuse_snapshot(self) -> dict[str, int]:
        with self._lock:
            return {ip: count for ip, count in self._failed_logins.items() if count >= 5}


auth_rate_limiter = AuthRateLimiter()
