from aiogram import F
from aiogram.filters import BaseFilter


class CallbackFilter(BaseFilter):
    def __init__(self, data: str | list):
        self.data = data

    async def __call__(self, _) -> bool:
        return F.data == self.data
