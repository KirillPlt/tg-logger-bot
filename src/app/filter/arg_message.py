import re
from re import Match, Pattern
from typing import Final, TypedDict

from aiogram.filters import BaseFilter
from aiogram.types import Message

MAX_COMMAND_NAME_LENGTH: Final[int] = 64


class ArgMessageData(TypedDict):
    arg1: str
    arg2: str


class ArgMessage(BaseFilter):
    regex: Pattern[str]

    def __init__(self, command: str) -> None:
        escaped_command: str = re.escape(command)
        self.regex = re.compile(
            rf"^{escaped_command}\s+([^\n]+?)\s*\n([\s\S]+)$"
        )

    async def __call__(self, message: Message) -> ArgMessageData | bool:
        text: str | None = message.text
        if text is None:
            return False

        match: Match[str] | None = self.regex.match(text)
        if match is None:
            return False

        arg1: str = match.group(1).strip()
        arg2: str = match.group(2).strip()

        if not arg1 or not arg2:
            return False

        if len(arg1) > MAX_COMMAND_NAME_LENGTH:
            return False

        data: ArgMessageData = {
            "arg1": arg1,
            "arg2": arg2,
        }
        return data