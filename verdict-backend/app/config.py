from functools import lru_cache

from pydantic import Field

from app.database_config import DatabaseSettings


class Settings(DatabaseSettings):
    asset_inventory_url: str = Field(default=...)
    cmdb_url: str = Field(default=...)

    debug: bool = False
    log_level: str = "info"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
