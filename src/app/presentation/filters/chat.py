from typing import Any

from aiogram.filters import BaseFilter


class ChatIdFilter(BaseFilter):
    def __init__(self, chat_id: int) -> None:
        self._chat_id = chat_id

    async def __call__(self, event: Any) -> bool:
        chat = getattr(event, "chat", None)
        if chat is not None:
            return bool(chat.id == self._chat_id)

        message = getattr(event, "message", None)
        if message is None:
            return False

        message_chat = getattr(message, "chat", None)
        return bool(message_chat is not None and message_chat.id == self._chat_id)
