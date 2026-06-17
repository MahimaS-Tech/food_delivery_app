from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Zomato-like Food Delivery API"
    ENVIRONMENT: str = Field(default="local", examples=["local", "test", "prod"])
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./food_delivery.db"
    AUTO_CREATE_TABLES: bool = True

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    TAX_RATE_BPS: int = 500  # 5% tax, expressed in basis points.
    DEFAULT_DELIVERY_FEE_CENTS: int = 3000
    MAX_PAGE_LIMIT: int = 100

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    CACHE_TTL_SECONDS: int = 30
    REDIS_URL: str | None = None

    REQUEST_TIMEOUT_SECONDS: int = 3

    def cors_origin_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
