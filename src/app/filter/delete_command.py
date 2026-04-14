import re
from re import Match, Pattern
from typing import Final, TypedDict

from aiogram.filters import BaseFilter
from aiogram.types import Message

MAX_COMMAND_NAME_LENGTH: Final[int] = 64


class DeleteCommandData(TypedDict):
    arg1: str


class DeleteCommandFilter(BaseFilter):
    regex: Pattern[str]

    def __init__(self, command: str) -> None:
        escaped_command: str = re.escape(command)
        self.regex = re.compile(rf"^{escaped_command}\s+([^\n]+?)\s*$")

    async def __call__(self, message: Message) -> DeleteCommandData | bool:
        text: str | None = message.text
        if text is None:
            return False

        match: Match[str] | None = self.regex.match(text)
        if match is None:
            return False

        arg1: str = match.group(1).strip()
        if not arg1:
            return False

        if len(arg1) > MAX_COMMAND_NAME_LENGTH:
            return False

        data: DeleteCommandData = {
            "arg1": arg1,
        }
        return data
