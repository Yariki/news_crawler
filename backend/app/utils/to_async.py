

import asyncio


async def to_thread(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)

async def sleep(seconds: int) -> None:
    """Asynchronous sleep function that allows other tasks to run while waiting for the specified number of seconds."""
    await asyncio.sleep(seconds)
