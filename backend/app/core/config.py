from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "news-monitor"
    database_url: str = Field(alias="DATABASE_URL")
    elasticsearch_url: str = Field(alias="ELASTICSEARCH_URL")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    default_keywords: str = Field(
        default="war,attack,missile,drone,война,атака,обстрел,удар,дрон",
        alias="DEFAULT_KEYWORDS",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def default_keywords_list(self) -> list[str]:
        return [item.strip().lower() for item in self.default_keywords.split(",") if item.strip()]

    @property
    def alembic_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
