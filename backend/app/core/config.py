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
    access_token_ttl_seconds: int = Field(default=3600, alias="ACCESS_TOKEN_TTL_SECONDS")
    refresh_token_ttl_seconds: int = Field(default=604800, alias="REFRESH_TOKEN_TTL_SECONDS")
    password_reset_token_ttl_seconds: int = Field(default=3600, alias="PASSWORD_RESET_TOKEN_TTL_SECONDS")
    
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
