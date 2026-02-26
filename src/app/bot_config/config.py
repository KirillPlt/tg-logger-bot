import os
from enum import StrEnum
from typing import Final

from aiogram.enums import ParseMode
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from app.logger import get_logger, LogSetupPreset
from app.utils import shifted_id

logger = get_logger()

if not load_dotenv(dotenv_path='.env'):
    logger.critical("Can't load .env file")
    raise RuntimeError(".env file not loaded")


class EnvironmentType(StrEnum):
    DEV = 'dev'
    PROD = 'prod'

# --------- Getter .env
BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
CHAT_ID: Final[str] = os.getenv("CHAT_ID", "")
LOG_CHAT_ID: Final[str] = os.getenv("LOG_CHAT_ID", "0")
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "DEBUG").upper()
ENVIRONMENT: Final[EnvironmentType] = EnvironmentType(
    os.getenv("ENVIRONMENT", EnvironmentType.DEV)
)

LOGGER_PRESET = (
    LogSetupPreset.DEV_CONSOLE
    if ENVIRONMENT.DEV
    else LogSetupPreset.PRODUCTION
)


# --------- Bot config
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# xyi
# --------- Chat data | Const
SHIFTED_CHAT_ID: Final[int] = shifted_id(int(CHAT_ID))
SHIFTED_LOG_CHAT_ID: Final[int] = shifted_id(int(LOG_CHAT_ID))