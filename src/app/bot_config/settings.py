from pydantic import BaseModel, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseModel):
    token: SecretStr
    chat_id: int = Field(..., lt=0)
    log_chat_id: int = Field(..., lt=0)
    info_chat_admin_id: int = Field(..., lt=0)


class Settings(BaseSettings):
    bot: BotSettings

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")


settings = Settings()