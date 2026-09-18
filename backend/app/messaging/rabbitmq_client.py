
import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Tuple
from app.core.config import settings
import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message
from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustChannel,
    AbstractRobustConnection,
    AbstractRobustExchange,
    ConsumerTag,
)

from yarl import URL

from app.messaging.messages.base import to_dict

logger = logging.getLogger(__name__)


def _connection_url() -> URL:
    """Build the broker URL with an explicit heartbeat.

    aiormq only reads ``heartbeat`` from the URL query - passing it as a
    ``connect_robust`` keyword is silently dropped - so it has to be set here.
    """
    url = URL(settings.rabbitmq_url)
    if "heartbeat" in url.query:
        return url
    return url.update_query(heartbeat=str(settings.rabbitmq_heartbeat))

class RabbitMQClient:
    """RabbitMQ client for managing connections, exchanges, queues, and message publishing/consuming."""

    def __init__(self):
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractRobustChannel | None = None
        self._exchange: AbstractRobustExchange | None = None
        self._exchange_name = settings.news_monitor_exchange_name
        self._crawling_update_queue_name = settings.crawling_update_queue_name
        self._dlx_name = settings.dlx_name
        self._dlq_name = settings.dlq_name
        self._queue_cache: dict[str, Tuple[ConsumerTag, AbstractQueue]] = {}

    async def _stop_all_consumers(self):
        """Stop all active consumers by canceling their consumer tags."""
        for queue_name, (consumer_tag, queue) in self._queue_cache.items():
            try:
                await queue.cancel(consumer_tag)
                logger.info("Stopped consuming messages from queue: %s", queue_name)
            except Exception:
                # The channel may already be gone (broker drop, shutdown race); nothing left to cancel.
                logger.warning("Could not cancel consumer on queue %s", queue_name, exc_info=True)
        self._queue_cache.clear()

    async def _discard_connection(self):
        """Tear down the current connection so a robust one can't keep reconnecting in the background."""
        connection, self._connection = self._connection, None
        self._channel = None
        self._exchange = None
        self._queue_cache.clear()

        if connection is None or connection.is_closed:
            return
        try:
            await connection.close()
        except Exception:
            logger.warning("Error closing previous RabbitMQ connection", exc_info=True)

    async def connect(self):
        """Establish a connection to RabbitMQ and create a channel."""
        # A RobustConnection retries forever on its own, so a stale one has to be closed
        # explicitly or it lingers as a zombie reconnect loop for the life of the process.
        await self._discard_connection()
        try:
            self._connection = await aio_pika.connect_robust(_connection_url())
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=1)
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            await self._discard_connection()
            raise

    async def declare_infrastructure(self):
        """Declare the necessary exchanges, queues, and bindings for the application."""
        if not self._channel:
            raise RuntimeError("RabbitMQ channel is not initialized.")
        
        # Declare the dead-letter exchange and queue
        dlx = await self._channel.declare_exchange(
            self._dlx_name, ExchangeType.DIRECT, durable=True
        )
        dlq = await self._channel.declare_queue(
            self._dlq_name, durable=True
        )
        await dlq.bind(dlx, routing_key=self._dlq_name)
        
        # Declare the main exchange
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name, ExchangeType.DIRECT, durable=True
        )
        
        # Declare the job updates queue and bind it to the exchange
        job_update_queue = await self._channel.declare_queue(
            self._crawling_update_queue_name, durable=True,
            arguments={
                "x-dead-letter-exchange": self._dlx_name,
                "x-dead-letter-routing-key": self._dlq_name
            }
        )
        await job_update_queue.bind(self._exchange, routing_key=self._crawling_update_queue_name)
        
    @property
    def is_ready(self) -> bool:
        """Check if the RabbitMQ client is ready for publishing or consuming messages."""
        return self._connection is not None and not self._connection.is_closed and self._channel is not None and not self._channel.is_closed and self._exchange is not None
    
    async def close(self):
        """Close the RabbitMQ connection."""
        if self._connection is None or self._connection.is_closed:
            await self._discard_connection()
            return
        await self._stop_all_consumers()
        await self._discard_connection()

    async def publish(self, message_body: Any, routing_key: str | None = None):
        """Publish a message to the exchange with the specified routing key."""
        if not self.is_ready:
            raise RuntimeError("RabbitMQ client is not connected or exchange is not declared.")
        
        routing_key = routing_key or self._crawling_update_queue_name

        message = Message(
            body=json.dumps(to_dict(message_body), default=str).encode(),
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT
        )
        
        await self._exchange.publish(message, routing_key=routing_key)
        
    async def consume(self, queue_name: str, callback: Callable[[dict], Awaitable[None]]):
        """Consume messages from the specified queue and process them using the provided callback."""
        assert self._channel is not None, "Channel must be initialized before consuming messages."
        assert self._exchange is not None, "Exchange must be declared before consuming messages."
        
        
        queue = await self._channel.get_queue(queue_name, ensure=True)
        
        async def _on_message(message: AbstractIncomingMessage):
            async with message.process():
                payload = json.loads(message.body.decode())
                await callback(payload)
        
        consumer_tag = await queue.consume(_on_message)
        self._queue_cache[queue_name] = (consumer_tag, queue)
        logger.info("Started consuming messages from queue: %s", queue_name)
    
    async def cancel_consume(self, queue_name: str):
        """Cancel consuming messages from the specified queue."""
        if queue_name in self._queue_cache:
            consumer_tag, queue = self._queue_cache[queue_name]
            assert self._channel is not None, "Channel must be initialized before canceling consume."
            await queue.cancel(consumer_tag)
            del self._queue_cache[queue_name]
            logger.info("Stopped consuming messages from queue: %s", queue_name)
        

_rabbitmq_client: RabbitMQClient | None = None
_rabbitmq_client_lock = asyncio.Lock()

async def get_rabbitmq_client() -> RabbitMQClient:
    """Get a singleton instance of RabbitMQClient, (re)connecting if it is missing or no longer ready."""
    global _rabbitmq_client
    async with _rabbitmq_client_lock:
        if _rabbitmq_client is not None and _rabbitmq_client.is_ready:
            return _rabbitmq_client

        client = _rabbitmq_client or RabbitMQClient()
        try:
            # connect() discards any stale connection first, so reconnecting here
            # never leaves an orphaned robust connection retrying in the background.
            await client.connect()
            await client.declare_infrastructure()
        except Exception:
            # Don't leave a half-initialized client cached for future callers to reuse.
            _rabbitmq_client = None
            raise
        _rabbitmq_client = client
        return _rabbitmq_client


async def close_rabbitmq_client() -> None:
    """Close and drop the singleton client, if one was created."""
    global _rabbitmq_client
    async with _rabbitmq_client_lock:
        if _rabbitmq_client is None:
            return
        try:
            await _rabbitmq_client.close()
        finally:
            _rabbitmq_client = None
