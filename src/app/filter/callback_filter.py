from aiogram import F
from aiogram.filters import BaseFilter


class CallbackFilter(BaseFilter):
    def __init__(self, message: str | list):
        self.message = message

    async def __call__(self, _) -> bool:
        return F.data == self.message
