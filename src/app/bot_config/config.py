import os
from typing import Final

from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from app.utils import shifted_id


load_dotenv(dotenv_path='.env')


# --------- Getter .env
BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
CHAT_ID: Final[str] = os.getenv("CHAT_ID", "")
LOG_CHAT_ID: Final[str] = os.getenv("LOG_CHAT_ID", "0")
print(LOG_CHAT_ID)
print(CHAT_ID)


# --------- Bot config
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode='html')
)

# xyi
# --------- Chat data | Const
SHIFTED_CHAT_ID: Final[int] = shifted_id(int(CHAT_ID))
SHIFTED_LOG_CHAT_ID: Final[int] = shifted_id(int(LOG_CHAT_ID))