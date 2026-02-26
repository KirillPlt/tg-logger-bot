from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

dp = Dispatcher()

@dp.message(Command('start'))
async def start_handler(
        message: Message,
        shifted_chat_id: int,
        shifted_log_chat_id: int
) -> None:

    chat_permalink: str = f"tg://chat?id={shifted_chat_id}"
    log_chat_permalink: str = f"tg://chat?id={shifted_log_chat_id}"

    await message.answer(
        text="Приветствую! Я - логгер.\n\n"
             "Настройки:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💬 Чат", url=chat_permalink)],
                [InlineKeyboardButton(text="⚙️ Лог чат", url=log_chat_permalink)],
                [InlineKeyboardButton(text="Пинг!", callback_data='ping')],
            ]
        )
    )