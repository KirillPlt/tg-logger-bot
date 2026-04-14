from aiogram import Router
from aiogram.enums import ChatType
from aiogram.types import Message

from app.database.client import ClientDB
from app.filter import ChatTypeFilter
from app.filter.set_custom_command import SetCustomCommand
from app.filter.user import IsCreator


rt = Router()


@rt.message(
    SetCustomCommand(command="+приветствие"),
    IsCreator(),
    ChatTypeFilter(
        chat_type=[
            ChatType.PRIVATE,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ],
    ),
)
async def set_greetings_handler(message: Message, arg1: str, arg2: str) -> None:
    await ClientDB.greetings.add_greeting(text=arg1 + "\n" + arg2)
    await message.answer("✅ Приветствие успешно создано!")
