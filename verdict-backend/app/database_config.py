import os
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_VALID_ENVIRONMENTS = {"development", "test", "production"}
_environment = os.getenv("ENVIRONMENT", "development")
if _environment not in _VALID_ENVIRONMENTS:
    raise ValueError(
        f"Invalid ENVIRONMENT {_environment!r}. "
        f"Must be one of: {', '.join(sorted(_VALID_ENVIRONMENTS))}"
    )


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[
            f".env.{_environment}",
            f".env.{_environment}.local",
        ],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    database_host: str = Field(default=...)
    database_port: int = Field(default=...)
    database_name: str = Field(default=...)
    database_user: str = Field(default=...)
    database_password: SecretStr = Field(default=...)

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{self.database_user}:{self.database_password.get_secret_value()}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()
