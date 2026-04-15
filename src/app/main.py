import asyncio
from contextlib import suppress

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bootstrap.container import build_container
from app.bootstrap.dispatcher import create_dispatcher
from app.config.settings import get_settings


async def main() -> None:
    settings = get_settings()
    settings.ensure_directories()

    container = build_container(settings)
    await container.database.initialize()
    await container.custom_command_service.prime_cache()

    bot = Bot(
        token=settings.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = create_dispatcher(settings, container)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


def run() -> None:
    with suppress(KeyboardInterrupt):
        asyncio.run(main())


if __name__ == "__main__":
    run()
