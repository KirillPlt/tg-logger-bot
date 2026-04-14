from typing import Final, TypedDict

from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.database.client import ClientDB

MAX_COMMAND_NAME_LENGTH: Final[int] = 64


class CustomCommandData(TypedDict):
    arg1: str
    arg2: str


class GetCustomCommand(BaseFilter):
    async def __call__(self, message: Message) -> CustomCommandData | bool:
        text: str | None = message.text
        if text is None:
            return False

        arg1: str = text.strip()
        if not arg1:
            return False

        if "\n" in arg1:
            return False

        if len(arg1) > MAX_COMMAND_NAME_LENGTH:
            return False

        arg2: str | None = await ClientDB.custom_command.get_custom_command(arg1)
        if arg2 is None:
            return False

        data: CustomCommandData = {
            "arg1": arg1,
            "arg2": arg2,
        }
        return data
