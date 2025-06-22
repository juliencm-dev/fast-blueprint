from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Starter Kit"
    VERSION: str
    PORT: int
    API_PREFIX: str
    ALLOWED_ORIGINS: List[str]
    ALLOWED_HOSTS: List[str]
    ALGORITHM: str
    FASTAPI_ENV: str
    DOMAIN_URL: str

    # Database Configuration
    DEV_DATABASE_URL: str
    PROD_DATABASE_URL: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    CACHE_EXPIRATION_TIME: int = 3600

    # Auth Configuration
    AUTH_SECRET: str
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Email Configuration (from env)
    MAIL_USERNAME: str | None
    MAIL_PASSWORD: str | None
    MAIL_FROM: str | None
    MAIL_PORT: int | str
    MAIL_SERVER: str | None
    MAIL_FROM_NAME: str | None

    model_config = SettingsConfigDict(
        env_file="./server/.env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
