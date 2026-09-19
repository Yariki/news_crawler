
import asyncio
import logging
import os
import threading
from typing import Any, Coroutine, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncRunner:
    """Owns a single long-lived event loop running in a background thread.

    Celery tasks are synchronous, so async work has to be driven from a sync call.
    Driving it with ``loop.run_until_complete`` per task leaves the loop stopped
    between tasks, which also freezes everything long-lived clients keep running in
    the background - most importantly the aio-pika heartbeat, so the broker tears
    the connection down while the worker sits idle. A loop that keeps running
    between tasks keeps those connections alive and reusable.
    """

    def __init__(self, thread_name: str = "celery-asyncio-loop"):
        self._thread_name = thread_name
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._pid: int | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """True when a loop thread is live in this process (never starts one)."""
        with self._lock:
            return self._is_usable

    @property
    def _is_usable(self) -> bool:
        return (
            self._loop is not None
            and not self._loop.is_closed()
            and self._thread is not None
            and self._thread.is_alive()
            # A prefork child inherits this object but not the parent's loop thread.
            and self._pid == os.getpid()
        )

    def _start(self) -> asyncio.AbstractEventLoop:
        """Start the loop thread. Caller must hold the lock."""
        loop = asyncio.new_event_loop()
        started = threading.Event()

        def _run() -> None:
            asyncio.set_event_loop(loop)
            loop.call_soon(started.set)
            try:
                loop.run_forever()
            finally:
                try:
                    _cancel_pending_tasks(loop)
                    loop.run_until_complete(loop.shutdown_asyncgens())
                finally:
                    loop.close()

        thread = threading.Thread(target=_run, name=self._thread_name, daemon=True)
        thread.start()
        started.wait()

        self._loop, self._thread, self._pid = loop, thread, os.getpid()
        logger.info("Started asyncio worker loop in thread '%s' (pid %s)", self._thread_name, self._pid)
        return loop

    def loop(self) -> asyncio.AbstractEventLoop:
        """Return the running worker loop, starting it on first use or after a fork."""
        with self._lock:
            if self._is_usable:
                assert self._loop is not None
                return self._loop
            self._loop = self._thread = self._pid = None
            return self._start()

    def run(self, coro: Coroutine[Any, Any, T], timeout: float | None = None) -> T:
        """Run a coroutine on the worker loop from a synchronous caller and wait for its result."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop()).result(timeout)

    def shutdown(self, timeout: float = 30.0) -> None:
        """Stop the worker loop and join its thread. Safe to call more than once."""
        with self._lock:
            loop, thread = self._loop, self._thread
            self._loop = self._thread = self._pid = None

        if loop is None or thread is None:
            return

        if not loop.is_closed():
            loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout)
        if thread.is_alive():
            logger.warning("Asyncio worker loop thread '%s' did not stop within %ss", self._thread_name, timeout)
        else:
            logger.info("Stopped asyncio worker loop thread '%s'", self._thread_name)


def _cancel_pending_tasks(loop: asyncio.AbstractEventLoop) -> None:
    """Cancel whatever is still scheduled so the loop can close without warnings."""
    pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
    if not pending:
        return
    for task in pending:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))


runner = AsyncRunner()


def run_async(coro: Coroutine[Any, Any, T], timeout: float | None = None) -> T:
    """Run a coroutine on the shared Celery worker loop."""
    return runner.run(coro, timeout)
