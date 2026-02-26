import asyncio

from app.bot_config.config import bot, CHAT_ID, SHIFTED_CHAT_ID, LOG_CHAT_ID, SHIFTED_LOG_CHAT_ID, LOG_LEVEL, LOGGER_PRESET
from app.callback import start_command_callback
from app.handler import events
from app.handler.start_ import dp
from app.logger import IwfLogger, get_logger

logger = get_logger()


async def main() -> None:
    logger.info("Starting up application")

    dp["chat_id"] = CHAT_ID
    dp["shifted_chat_id"] = SHIFTED_CHAT_ID
    dp["log_chat_id"] = LOG_CHAT_ID
    dp["shifted_log_chat_id"] = SHIFTED_LOG_CHAT_ID
    dp.include_routers(
        start_command_callback.rt,
        events.rt
    )

    logger.info("Aiogram workspace configured. Starting polling...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    IwfLogger.setup(LOG_LEVEL, LOGGER_PRESET)
    logger.debug("Logger configured")
    asyncio.run(main())
