import asyncio

from ..core.config import settings

async def run_dispatch_sources() -> int:
    """Retrieves a list of sources that are due for crawling and dispatches them for processing. It returns a list of Source objects that were dispatched."""
    while True:
        try:
            from .tasks.dispatch_sources import dispatch_sources
            dispatched_count = await dispatch_sources(settings.beat_batch_size)
            print(f"Dispatched {dispatched_count} sources for crawling.")
        except Exception as e:
            print(f"Error dispatching sources: {e}")
        
        await asyncio.sleep(settings.beat_tick_seconds)

def main() -> None:
    """Main function to run the dispatch_sources task in an infinite loop with a delay between each execution."""
    asyncio.run(run_dispatch_sources())

if __name__ == "__main__":
    main()
