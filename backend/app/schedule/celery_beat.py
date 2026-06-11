import asyncio
from ..core.config import settings
import logging
import os

app_mode = os.getenv("APP_MODE", "dev")

logging.basicConfig(level=logging.DEBUG if app_mode == "dev" else logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

async def run_dispatch_due_sources() -> int:
    """Retrieves a list of sources that are due for crawling and dispatches them for processing. It returns a list of Source objects that were dispatched."""
    while True:
        try:
            from .tasks.dispatch_sources import dispatch_due_sources
            dispatched_count = await dispatch_due_sources(settings.beat_batch_size)
            logger.info(f"Dispatched {dispatched_count} sources for crawling.")
        except Exception as e:
            logger.error(f"Error dispatching sources: {e}")

        await asyncio.sleep(settings.beat_tick_seconds)

def main() -> None:
    """Main function to run the dispatch_sources task in an infinite loop with a delay between each execution."""
    asyncio.run(run_dispatch_due_sources())

if __name__ == "__main__":
    main()
