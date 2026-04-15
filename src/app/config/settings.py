from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseModel):
    token: SecretStr
    chat_id: int = Field(..., lt=0)
    log_chat_id: int = Field(..., lt=0)
    info_chat_admin_id: int = Field(..., lt=0)
    owner_id: int = 5070279413
    log_chat_invite_url: str = "https://t.me/+gPmxiepnJWFhMjAy"
    info_chat_admin_invite_url: str = "https://t.me/+eDiObhj7a6wyZGU6"


class DatabaseSettings(BaseModel):
    path: Path = Path("data/bot.db")


class RuntimeSettings(BaseModel):
    timezone: str = "Europe/Moscow"
    admin_cache_ttl_seconds: int = Field(default=60, ge=5, le=3600)


class LoggingSettings(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    json_logs: bool = Field(default=True, alias="json")
    step_debug_enabled: bool = False


class MetricsSettings(BaseModel):
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = Field(default=9000, ge=1, le=65535)


class Settings(BaseSettings):
    bot: BotSettings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    metrics: MetricsSettings = Field(default_factory=MetricsSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    def ensure_directories(self) -> None:
        self.database.path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
