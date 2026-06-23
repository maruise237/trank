"""Centralised settings read from environment (Dokploy injects these)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    # DataForSEO
    dataforseo_login: str
    dataforseo_password: str
    dataforseo_api_url: str = "https://api.dataforseo.com/v3"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_timezone: str = "Europe/Paris"

    # App
    digest_delta_threshold: int = 5
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
