from aiogram import Router, types
from aiogram.enums import ChatType

from app.filter import ChatTypeFilter
from app.filter import CallbackFilter


rt = Router()


@rt.callback_query(
    CallbackFilter(data="ping"),
    ChatTypeFilter([ChatType.PRIVATE])
)
async def start_callback(c: types.CallbackQuery) -> None:
    await c.answer()
    await c.message.answer("🎾 Понг!")
