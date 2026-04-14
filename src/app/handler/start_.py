from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from app.bot_config.config import CHAT_ID
from app.filter.user import IsCreator
from app.handler.events import ChatIdFilter


dp = Dispatcher()


@dp.message(Command("start"), ChatIdFilter, IsCreator())
async def start_handler(
    message: Message,
    shifted_chat_id: int,
) -> None:

    chat_permalink: str = f"tg://chat?id={shifted_chat_id}"

    msg = await message.answer(
        text="⚠️ Администрация чата, просим вас вступить в логгер-чат для удобства отчетов о группе.\n"
        "Вход доступен только для администрации чата, поэтому иные пользователи не пройдут проверку и бот не пропустит "
        "в логгер-чат посторонних.\n"
        "Так же здесь имеется информационный чат для администрации. Вход так же доступен <b>только</b> для админов.\n\n"
        "ℹ️ Информация:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💬 Чат", url=chat_permalink)],
                [
                    InlineKeyboardButton(
                        text="⚙️ Лог чат", url="https://t.me/+gPmxiepnJWFhMjAy"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛡 Инфо-админ", url="https://t.me/+eDiObhj7a6wyZGU6"
                    )
                ],
            ]
        ),
    )

    await message.bot.pin_chat_message(
        chat_id=int(CHAT_ID), message_id=msg.message_id, disable_notification=True
    )
