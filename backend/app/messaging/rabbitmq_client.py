
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

logger = logging.getLogger(__name__)

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
            assert self._channel is not None, "Channel must be initialized before stopping consumers."
            await queue.cancel(consumer_tag)
            logger.info("Stopped consuming messages from queue: %s", queue_name)
        self._queue_cache.clear()
    
    
    async def connect(self):
        """Establish a connection to RabbitMQ and create a channel."""
        try:
            self._connection = await aio_pika \
                .connect_robust(settings.rabbitmq_url)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=1)
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
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
        await dlq.bind(dlx, routing_key=self._dl_routing_key)
        
        # Declare the main exchange
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name, ExchangeType.DIRECT, durable=True
        )
        
        # Declare the job updates queue and bind it to the exchange
        job_update_queue = await self._channel.declare_queue(
            self._crawling_update_queue_name, durable=True,
            arguments={
                "x-dead-letter-exchange": self._dlx_name,
                "x-dead-letter-routing-key": self._dl_routing_key,
            }
        )
        await job_update_queue.bind(self._exchange, routing_key=self._job_update_routing_key)
        
    @property
    def is_ready(self) -> bool:
        """Check if the RabbitMQ client is ready for publishing or consuming messages."""
        return self._connection is not None and not self._connection.is_closed and self._channel is not None and not self._channel.is_closed and self._exchange is not None
    
    async def close(self):
        """Close the RabbitMQ connection."""
        if self._connection and self._connection.is_closed:
            return
        await self._stop_all_consumers()
        await self._connection.close()
        self._connection = None
        self._channel = None
        self._exchange = None
    
    async def publish(self, routing_key: str, message_body: dict[str, Any]):
        """Publish a message to the exchange with the specified routing key."""
        if not self.is_ready:
            raise RuntimeError("RabbitMQ client is not connected or exchange is not declared.")
        
        message = Message(
            body=json.dumps(message_body).encode(),
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
        