from time import perf_counter

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from app.application.services import BotRuntimeSettingsService
from app.config import Settings
from app.infrastructure.observability import MetricsCollector, get_logger, log_step
from app.presentation.filters import OwnerFilter


ALLOWED_CHAT_TYPES = {ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP}


def create_runtime_control_router(settings: Settings) -> Router:
    router = Router(name="runtime-controls")
    owner_filter = OwnerFilter(settings.bot.owner_id)
    logger = get_logger(__name__)

    @router.message(
        F.text.regexp(r"^\s*\+реакции\s*$"),
        owner_filter,
        F.chat.type.in_(ALLOWED_CHAT_TYPES),
    )
    async def enable_reaction_logs_handler(
        message: Message,
        bot_runtime_settings_service: BotRuntimeSettingsService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        _, was_changed = await bot_runtime_settings_service.set_reaction_logging_enabled(True)
        await message.answer(_format_reaction_logging_toggle_response(True, was_changed))
        metrics.observe_handler(
            handler="runtime_controls.enable_reaction_logs_handler",
            status="success" if was_changed else "unchanged",
            duration_seconds=perf_counter() - started_at,
        )
        log_step(
            logger,
            "reaction_logs_enabled_command_processed",
            handler="runtime_controls.enable_reaction_logs_handler",
            actor_user_id=message.from_user.id if message.from_user is not None else None,
            changed=was_changed,
        )

    @router.message(
        F.text.regexp(r"^\s*\-реакции\s*$"),
        owner_filter,
        F.chat.type.in_(ALLOWED_CHAT_TYPES),
    )
    async def disable_reaction_logs_handler(
        message: Message,
        bot_runtime_settings_service: BotRuntimeSettingsService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        _, was_changed = await bot_runtime_settings_service.set_reaction_logging_enabled(False)
        await message.answer(_format_reaction_logging_toggle_response(False, was_changed))
        metrics.observe_handler(
            handler="runtime_controls.disable_reaction_logs_handler",
            status="success" if was_changed else "unchanged",
            duration_seconds=perf_counter() - started_at,
        )
        log_step(
            logger,
            "reaction_logs_disabled_command_processed",
            handler="runtime_controls.disable_reaction_logs_handler",
            actor_user_id=message.from_user.id if message.from_user is not None else None,
            changed=was_changed,
        )

    return router


def _format_reaction_logging_toggle_response(enabled: bool, changed: bool) -> str:
    if enabled:
        title = "✅ <b>Логи реакций включены.</b>"
        details = (
            "😀 Теперь бот снова будет отправлять в лог-чат все обновления по реакциям."
            if changed
            else "😀 Логи реакций уже были включены и продолжают работать."
        )
    else:
        title = "⛔ <b>Логи реакций выключены.</b>"
        details = (
            "🤫 Бот больше не будет отправлять в лог-чат обновления по реакциям."
            if changed
            else "🤫 Логи реакций уже были выключены."
        )

    return f"{title}\n\n{details}"
