import os
from typing import Final

from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from app.utils import shifted_id


load_dotenv(dotenv_path='.botenv')


# --------- Getter .botenv
BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
print(BOT_TOKEN)
CHAT_ID: Final[str] = os.getenv("CHAT_ID", 0)
LOG_CHAT_ID: Final[str] = os.getenv("MANAGER_IDS", "")


# --------- Bot config
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode='html')
)

# --------- Chat data | Const
SHIFTED_CHAT_ID: Final[int] = shifted_id(CHAT_ID)
SHIFTED_LOG_CHAT_ID: Final[int] = shifted_id(LOG_CHAT_ID)