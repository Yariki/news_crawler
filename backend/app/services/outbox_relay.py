
import asyncio


from app.db.session import AsyncSessionLocal
from app.messaging.messages.keywords_match import KeywordsMatchMessage
from app.messaging.rabbitmq_client import RabbitMQClient
from app.models.outbox_event_type import OutboxEventType
from app.repositories.outbox_repository import OutboxRepository
from app.services.es import ElasticService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class OutboxRelay:
    """Service responsible for relaying messages from the outbox to RabbitMQ and Elasticsearch."""
    
    def __init__(self, elasticsearch_client: ElasticService, rabbitmq_client: RabbitMQClient):
        self._elasticsearch_client = elasticsearch_client
        self._rabbitmq_client = rabbitmq_client
        self._stopping = asyncio.Event()

    def stop(self) -> None:
        """Signal the relay to stop processing messages."""
        self._stopping.set()
        
    async def run_forever(self) -> None:
        """Continuously relay messages from the outbox to RabbitMQ and Elasticsearch."""
        while not self._stopping.is_set():
            try:
                processed = await self._run_once()
            except Exception as e:
                logger.error(f"Error running outbox relay: {e}")
                processed = 0
            if processed == 0:
                await asyncio.sleep(settings.outbox_poll_interval_seconds)
    
    async def _run_once(self) -> int:
        async with AsyncSessionLocal() as session:
            repo = OutboxRepository(session)
            events = await repo.claim_batch(limit=settings.outbox_batch_size)
            
            for event in events:
                try:
                    await self._dispatch_event(event)
                    repo.mark_as_processed(event)
                except Exception as e:
                    logger.error(f"Error processing event ID {event.id}: {e}")
                    repo.mark_as_failed(event, settings.outbox_backoff_base_seconds, settings.outbox_max_attempts, str(e) )
            await session.commit()
            return len(events)
        
    async def _dispatch_event(self, event) -> None:
        if event.event_type == OutboxEventType.ARTICLE_INDEX:
            await self._elasticsearch_client.index_article(event.payload)
        elif event.event_type == OutboxEventType.KEYWORDS_MATCH:
            message = KeywordsMatchMessage(**event.payload)
            await self._rabbitmq_client.publish(message)
        else:
            logger.warning(f"Unknown event type: {event.event_type}. Event ID: {event.id}")