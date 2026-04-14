import re
from re import Match, Pattern
from typing import Final, TypedDict

from aiogram.filters import BaseFilter
from aiogram.types import Message

MAX_COMMAND_NAME_LENGTH: Final[int] = 64


class SetCustomCommandData(TypedDict):
    arg1: str  # имя команды
    arg2: str  # текст с HTML


class SetCustomCommand(BaseFilter):
    regex: Pattern[str]

    def __init__(self, command: str) -> None:
        escaped_command: str = re.escape(command)
        self.regex = re.compile(
            rf"^{escaped_command}\s+([^\n]+?)\s*\n([\s\S]+)$"
        )

    async def __call__(self, message: Message) -> SetCustomCommandData | bool:
        plain_text: str | None = message.text
        html_text: str | None = message.html_text

        if plain_text is None or html_text is None:
            return False

        match: Match[str] | None = self.regex.match(plain_text)
        if match is None:
            return False

        # --- arg1 (без форматирования)
        arg1: str = match.group(1).strip()

        if not arg1:
            return False

        if len(arg1) > MAX_COMMAND_NAME_LENGTH:
            return False

        # --- arg2 (с HTML форматированием)
        # делим HTML-текст по первой строке
        parts: list[str] = html_text.split("\n", maxsplit=1)
        if len(parts) < 2:
            return False

        arg2: str = parts[1].strip()

        if not arg2:
            return False

        data: SetCustomCommandData = {
            "arg1": arg1,
            "arg2": arg2,
        }
        return data