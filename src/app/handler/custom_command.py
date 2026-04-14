import aiosqlite
from aiogram import Router
from aiogram.enums import ChatType
from aiogram.types import Message

from app.bot_config.config import CHAT_ID, LOG_CHAT_ID, INFO_CHAT_ADMIN_ID
from app.db import save_custom_command, delete_custom_command
from app.filter import ChatTypeFilter
from app.filter.arg_message import ArgMessage
from app.filter.chat import ChatId
from app.filter.delete_command import DeleteCommandFilter
from app.filter.get_custom_command import GetCustomCommand
from app.filter.user import IsCreator


ChatIdFilter = ChatId(int(CHAT_ID))
LogChatIdFilter = ChatId(int(LOG_CHAT_ID))
InfoChatAdminFilter = ChatId(int(INFO_CHAT_ADMIN_ID))

rt = Router()


@rt.message(
    ArgMessage("+команда"),
    IsCreator(),
    ChatTypeFilter(
        chat_type=[
            ChatType.PRIVATE,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ],
    ),
)
async def set_custom_command_handler(message: Message, arg1: str, arg2: str) -> None:
    await save_custom_command(arg1, arg2)

    await message.answer(f"Команда {arg1} успешно создана!")
    await message.answer(f"Ваш текст:\n{arg2}")


@rt.message(
    GetCustomCommand(),
    ChatTypeFilter(
        chat_type=[
            ChatType.PRIVATE,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ],
    ),
)
async def get_custom_command_handler(message: Message, arg1: str, arg2: str) -> None:
    await message.answer(arg2)


@rt.message(
    DeleteCommandFilter(r"-команда"),
    IsCreator(),
    ChatTypeFilter(
        chat_type=[
            ChatType.PRIVATE,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ],
    )
)
async def delete_custom_command_handler(message: Message, arg1: str) -> None:
    success: bool = await delete_custom_command(arg1)

    if success:
        await message.answer(f"Команда {arg1} удалена ✅")
    else:
        await message.answer(f"Команда {arg1} не найдена ❌")