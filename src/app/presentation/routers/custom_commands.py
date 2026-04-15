from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from app.application.services import CustomCommandService
from app.config import Settings
from app.presentation.filters import OwnerFilter
from app.presentation.parsers import (
    LIST_COMMANDS_REQUEST,
    parse_create_command,
    parse_delete_command,
)


ALLOWED_CHAT_TYPES = {ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP}
CREATE_USAGE_TEXT = (
    "Формат создания команды:\n"
    "<code>+команда имя команды</code>\n"
    "<code>текст ответа</code>"
)
DELETE_USAGE_TEXT = "Формат удаления команды: <code>-команда имя команды</code>"


def create_custom_command_router(settings: Settings) -> Router:
    router = Router(name="custom-commands")
    owner_filter = OwnerFilter(settings.bot.owner_id)

    @router.message(F.text.startswith("+команда"), owner_filter, F.chat.type.in_(ALLOWED_CHAT_TYPES))
    async def set_custom_command_handler(
        message: Message,
        custom_command_service: CustomCommandService,
    ) -> None:
        parsed_command = parse_create_command(message.text, message.html_text)
        if parsed_command is None:
            await message.answer(CREATE_USAGE_TEXT)
            return

        try:
            result = await custom_command_service.save(
                parsed_command.name,
                parsed_command.response_html,
            )
        except ValueError as error:
            await message.answer(f"❌ {error}")
            return

        action = "создана" if result.was_created else "обновлена"
        await message.answer(
            f"✅ Команда \"{result.command.display_name}\" успешно {action}."
        )

    @router.message(F.text == LIST_COMMANDS_REQUEST, owner_filter, F.chat.type.in_(ALLOWED_CHAT_TYPES))
    async def list_custom_commands_handler(
        message: Message,
        custom_command_service: CustomCommandService,
    ) -> None:
        commands = await custom_command_service.list_commands()
        if not commands:
            await message.answer("Список кастомных команд пуст.")
            return

        commands_text = "\n".join(
            f"{index}. <code>{command.display_name}</code>"
            for index, command in enumerate(commands, start=1)
        )
        await message.answer(
            "Доступные кастомные команды:\n"
            f"{commands_text}"
        )

    @router.message(F.text.startswith("-команда"), owner_filter, F.chat.type.in_(ALLOWED_CHAT_TYPES))
    async def delete_custom_command_handler(
        message: Message,
        custom_command_service: CustomCommandService,
    ) -> None:
        command_name = parse_delete_command(message.text)
        if command_name is None:
            await message.answer(DELETE_USAGE_TEXT)
            return

        try:
            is_deleted = await custom_command_service.delete(command_name)
        except ValueError as error:
            await message.answer(f"❌ {error}")
            return

        if is_deleted:
            await message.answer(f"✅ Команда \"{command_name}\" удалена.")
            return

        await message.answer(f"❌ Команда \"{command_name}\" не найдена.")

    @router.message(F.text, F.chat.type.in_(ALLOWED_CHAT_TYPES))
    async def get_custom_command_handler(
        message: Message,
        custom_command_service: CustomCommandService,
    ) -> None:
        if message.text is None:
            return

        try:
            command = await custom_command_service.resolve(message.text)
        except ValueError:
            return

        if command is None:
            return

        await message.answer(command.response_html)

    return router
