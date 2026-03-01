import asyncio
import logging
from contextlib import suppress

from app.bot_config.config import bot, CHAT_ID, SHIFTED_CHAT_ID, LOG_CHAT_ID, SHIFTED_LOG_CHAT_ID
from app.callback import start_command_callback
from app.handler import events
from app.handler.start_ import dp


logging.basicConfig(level=logging.NOTSET)


async def main() -> None:
    dp["chat_id"] = CHAT_ID
    dp["shifted_chat_id"] = SHIFTED_CHAT_ID
    dp["log_chat_id"] = LOG_CHAT_ID
    dp["shifted_log_chat_id"] = SHIFTED_LOG_CHAT_ID
    dp.include_routers(
        start_command_callback.rt,
        events.rt
    )

    await dp.start_polling(bot)

if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
