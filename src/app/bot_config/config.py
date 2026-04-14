from typing import Final

from aiogram.enums import ParseMode
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from app.utils import shifted_id
from app.bot_config.settings import settings


# --------- Getter .env
BOT_TOKEN: Final[str] = settings.bot.token.get_secret_value()
CHAT_ID: Final[int] = settings.bot.chat_id
LOG_CHAT_ID: Final[int] = settings.bot.log_chat_id
INFO_CHAT_ADMIN_ID: Final[int] = settings.bot.info_chat_admin_id


# --------- Bot config
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


# --------- Chat data | Const
SHIFTED_CHAT_ID: Final[int] = shifted_id(CHAT_ID)
SHIFTED_LOG_CHAT_ID: Final[int] = shifted_id(LOG_CHAT_ID)
