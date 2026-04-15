from time import perf_counter

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from app.application.services import CustomCommandService
from app.config import Settings
from app.infrastructure.observability import MetricsCollector, get_logger, log_step
from app.presentation.filters import OwnerFilter
from app.presentation.parsers import (
    LIST_COMMANDS_REQUEST,
    parse_create_command,
    parse_delete_command,
)


ALLOWED_CHAT_TYPES = {ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP}
CREATE_USAGE_TEXT = (
    "🛠 <b>Создание кастомной команды</b>\n\n"
    "Первая строка:\n"
    "<code>+команда имя команды</code>\n\n"
    "Вторая строка:\n"
    "текст ответа"
)
DELETE_USAGE_TEXT = (
    "🗑 <b>Удаление кастомной команды</b>\n\n"
    "Используй формат:\n"
    "<code>-команда имя команды</code>"
)


def create_custom_command_router(settings: Settings) -> Router:
    router = Router(name="custom-commands")
    owner_filter = OwnerFilter(settings.bot.owner_id)
    logger = get_logger(__name__)

    @router.message(F.text.startswith("+команда"), owner_filter, F.chat.type.in_(ALLOWED_CHAT_TYPES))
    async def set_custom_command_handler(
        message: Message,
        custom_command_service: CustomCommandService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        log_step(
            logger,
            "custom_command_create_requested",
            handler="custom_commands.set_custom_command_handler",
            actor_user_id=message.from_user.id if message.from_user is not None else None,
        )
        parsed_command = parse_create_command(message.text, message.html_text)
        if parsed_command is None:
            await message.answer(CREATE_USAGE_TEXT)
            metrics.observe_handler(
                handler="custom_commands.set_custom_command_handler",
                status="invalid_input",
                duration_seconds=perf_counter() - started_at,
            )
            return

        try:
            result = await custom_command_service.save(
                parsed_command.name,
                parsed_command.response_html,
            )
        except ValueError as error:
            await message.answer(
                "❌ <b>Не удалось сохранить команду.</b>\n\n"
                f"{error}"
            )
            metrics.observe_handler(
                handler="custom_commands.set_custom_command_handler",
                status="validation_error",
                duration_seconds=perf_counter() - started_at,
            )
            return

        action = "создана" if result.was_created else "обновлена"
        await message.answer(
            "✅ <b>Команда успешно сохранена.</b>\n\n"
            f"🧩 Имя: <code>{result.command.display_name}</code>\n"
            f"📝 Статус: <b>{action}</b>"
        )
        metrics.observe_handler(
            handler="custom_commands.set_custom_command_handler",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )

    @router.message(F.text == LIST_COMMANDS_REQUEST, owner_filter, F.chat.type.in_(ALLOWED_CHAT_TYPES))
    async def list_custom_commands_handler(
        message: Message,
        custom_command_service: CustomCommandService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        commands = await custom_command_service.list_commands()
        if not commands:
            await message.answer(
                "📭 <b>Список кастомных команд пуст.</b>\n\n"
                "Пока что здесь нет ни одной сохраненной команды."
            )
            metrics.observe_handler(
                handler="custom_commands.list_custom_commands_handler",
                status="empty",
                duration_seconds=perf_counter() - started_at,
            )
            return

        commands_text = "\n".join(
            f"{index}. <code>{command.display_name}</code>"
            for index, command in enumerate(commands, start=1)
        )
        await message.answer(
            "📚 <b>Доступные кастомные команды</b>\n\n"
            f"{commands_text}"
        )
        metrics.observe_handler(
            handler="custom_commands.list_custom_commands_handler",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )

    @router.message(F.text.startswith("-команда"), owner_filter, F.chat.type.in_(ALLOWED_CHAT_TYPES))
    async def delete_custom_command_handler(
        message: Message,
        custom_command_service: CustomCommandService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        command_name = parse_delete_command(message.text)
        if command_name is None:
            await message.answer(DELETE_USAGE_TEXT)
            metrics.observe_handler(
                handler="custom_commands.delete_custom_command_handler",
                status="invalid_input",
                duration_seconds=perf_counter() - started_at,
            )
            return

        try:
            is_deleted = await custom_command_service.delete(command_name)
        except ValueError as error:
            await message.answer(
                "❌ <b>Не удалось удалить команду.</b>\n\n"
                f"{error}"
            )
            metrics.observe_handler(
                handler="custom_commands.delete_custom_command_handler",
                status="validation_error",
                duration_seconds=perf_counter() - started_at,
            )
            return

        if is_deleted:
            await message.answer(
                "✅ <b>Команда удалена.</b>\n\n"
                f"🧩 Имя: <code>{command_name}</code>"
            )
            metrics.observe_handler(
                handler="custom_commands.delete_custom_command_handler",
                status="success",
                duration_seconds=perf_counter() - started_at,
            )
            return

        await message.answer(
            "❌ <b>Команда не найдена.</b>\n\n"
            f"🧩 Имя: <code>{command_name}</code>"
        )
        metrics.observe_handler(
            handler="custom_commands.delete_custom_command_handler",
            status="not_found",
            duration_seconds=perf_counter() - started_at,
        )

    @router.message(F.text, F.chat.type.in_(ALLOWED_CHAT_TYPES))
    async def get_custom_command_handler(
        message: Message,
        custom_command_service: CustomCommandService,
        metrics: MetricsCollector,
    ) -> None:
        if message.text is None:
            return

        started_at = perf_counter()
        try:
            command = await custom_command_service.resolve(message.text)
        except ValueError:
            return

        if command is None:
            metrics.observe_handler(
                handler="custom_commands.get_custom_command_handler",
                status="miss",
                duration_seconds=perf_counter() - started_at,
            )
            return

        await message.answer(command.response_html)
        metrics.observe_handler(
            handler="custom_commands.get_custom_command_handler",
            status="hit",
            duration_seconds=perf_counter() - started_at,
        )

    return router
