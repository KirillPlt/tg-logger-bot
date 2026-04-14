from collections.abc import Sequence

from aiogram import types
from aiogram.filters import BaseFilter
from aiogram.enums import ChatType


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: Sequence[ChatType]):
        self.chat_type = chat_type

    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        if isinstance(event, types.CallbackQuery):
            return event.message.chat.type in self.chat_type
        return event.chat.type in self.chat_type


class ChatId(BaseFilter):
    def __init__(self, chat_id: int):
        self.chat_id = chat_id

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.id == self.chat_id
