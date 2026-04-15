import asyncio
from contextlib import suppress
from time import perf_counter

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bootstrap.container import build_container
from app.bootstrap.dispatcher import create_dispatcher
from app.config.settings import get_settings
from app.infrastructure.observability import get_logger, log_step, setup_logging


async def main() -> None:
    settings = get_settings()
    setup_logging(
        level_name=settings.logging.level,
        json_logs=settings.logging.json_logs,
    )
    logger = get_logger(__name__)
    startup_started_at = perf_counter()
    settings.ensure_directories()
    log_step(logger, "application_starting")

    container = build_container(settings)
    if settings.metrics.enabled:
        container.metrics.start_server(
            host=settings.metrics.host,
            port=settings.metrics.port,
        )
        log_step(
            logger,
            "metrics_server_started",
            metrics_host=settings.metrics.host,
            metrics_port=settings.metrics.port,
        )

    await container.database.initialize()
    await container.custom_command_service.prime_cache()

    bot = Bot(
        token=settings.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = create_dispatcher(settings, container)
    allowed_updates = dispatcher.resolve_used_update_types()
    log_step(
        logger,
        "polling_starting",
        allowed_updates=allowed_updates,
        startup_duration_ms=round((perf_counter() - startup_started_at) * 1000, 3),
    )

    try:
        await dispatcher.start_polling(bot, allowed_updates=allowed_updates)
    finally:
        log_step(logger, "polling_stopping")
        await bot.session.close()


def run() -> None:
    with suppress(KeyboardInterrupt):
        asyncio.run(main())


if __name__ == "__main__":
    run()
