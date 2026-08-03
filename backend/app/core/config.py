from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.env_settings import get_env_file


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=get_env_file(), extra="ignore")

    app_name: str = "news-monitor"
    database_url: str = Field(alias="DATABASE_URL")
    elasticsearch_url: str = Field(alias="ELASTICSEARCH_URL")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    default_keywords: str = Field(alias="DEFAULT_KEYWORDS")
    app_mode: str = Field(default="prod", alias="APP_MODE")
    crawl_delay: int = Field(default=5, alias="CRAWL_DELAY")
    request_rate: int = Field(default=10, alias="REQUEST_RATE")
    telegram_api_id: str = Field(default="", alias="TELEGRAM_API_ID")
    telegram_api_hash: str = Field(default="", alias="TELEGRAM_API_HASH")
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/", alias="RABBITMQ_URL")
    celery_task_queue: str = Field(default="scheduler.checks", alias="CELERY_TASK_QUEUE")
    checker_timeout_seconds: float = Field(default=30.0, alias="CHECKER_TIMEOUT_SECONDS")
    beat_tick_seconds: int = Field(default=10, alias="BEAT_TICK_SECONDS")
    beat_batch_size: int = Field(default=50, alias="BEAT_BATCH_SIZE")
    
    news_monitor_exchange_name: str = Field(default="news_monitor_updates", alias="NEWS_MONITOR_EXCHANGE_NAME")
    crawling_update_queue_name: str = Field(default="crawling_update", alias="CRAWLING_UPDATE_QUEUE_NAME")

    dlx_name: str = Field(default="news_monitor_dlx", alias="DLX_NAME")
    dlq_name: str = Field(default="news_monitor_dlx_queue", alias="DLQ_NAME")
    
    outbox_poll_interval_seconds: int = Field(default=5, alias="OUTBOX_POLL_INTERVAL_SECONDS")
    outbox_batch_size: int = Field(default=50, alias="OUTBOX_BATCH_SIZE")
    outbox_backoff_base_seconds: int = Field(default=10, alias="OUTBOX_BACKOFF_BASE_SECONDS")
    outbox_max_attempts: int = Field(default=8, alias="OUTBOX_MAX_ATTEMPTS")

    security_key: str = Field(
        default="*args, **kwargs",
        alias="SECURITY_KEY",
    )

    algorithm: str = Field(
        default="HS256",
        alias="ALGORITHM",
    )

    access_ttl_minutes: int = Field(default=60 * 11, alias="ACCESS_TTL_MINUTES")
    refresh_ttl_minutes: int = Field(default=60 * 24 * 7, alias="REFRESH_TTL_MINUTES")
    issuer: str = Field(default="News Crawler", alias="ISSUER")

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def default_keywords_list(self) -> list[str]:
        return [
            item.strip().lower()
            for item in self.default_keywords.split(",")
            if item.strip()
        ]

    @property
    def alembic_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
