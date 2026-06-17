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
    celery_broker_url: str = Field(default="amqp://guest:guest@localhost:5672/", alias="CELERY_BROKER_URL")
    celery_task_queue: str = Field(default="scheduler.checks", alias="CELERY_TASK_QUEUE")
    checker_timeout_seconds: float = Field(default=30.0, alias="CHECKER_TIMEOUT_SECONDS")
    beat_tick_seconds: int = Field(default=10, alias="BEAT_TICK_SECONDS")
    beat_batch_size: int = Field(default=50, alias="BEAT_BATCH_SIZE")
    
    news_monitor_exchange_name: str = Field(default="news_monitor_updates", alias="NEWS_MONITOR_EXCHANGE_NAME")
    job_update_queue_name: str = Field(default="jobs_updates_queue", alias="JOB_UPDATE_QUEUE_NAME")
    job_update_routing_key: str = Field(default="jobs.update", alias="JOB_UPDATE_ROUTING_KEY")
    
    dlx_name: str = Field(default="news_monitor_dlx", alias="DLX_NAME")
    dlq_name: str = Field(default="news_monitor_dlq", alias="DLQ_NAME")
    dl_routing_key: str = Field(default="news_monitor.dlq", alias="DL_ROUTING_KEY")
    
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
