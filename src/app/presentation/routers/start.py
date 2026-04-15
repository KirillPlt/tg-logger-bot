from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import Settings
from app.presentation.filters import ChatIdFilter, OwnerFilter
from app.presentation.keyboards import build_start_message_keyboard


START_MESSAGE_TEXT = (
    "⚠️ Администрация чата, просим вас вступить в логгер-чат для удобства отчетов о группе.\n"
    "Вход доступен только для администрации чата, поэтому иные пользователи не пройдут проверку "
    "и бот не пропустит в логгер-чат посторонних.\n"
    "Также здесь имеется информационный чат для администрации. Вход туда доступен "
    "<b>только</b> для админов.\n\n"
    "ℹ️ Информация:"
)


def create_start_router(settings: Settings) -> Router:
    router = Router(name="start")
    router.message.filter(ChatIdFilter(settings.bot.chat_id))

    @router.message(Command("start"), OwnerFilter(settings.bot.owner_id))
    async def start_handler(message: Message, bot: Bot) -> None:
        sent_message = await message.answer(
            text=START_MESSAGE_TEXT,
            reply_markup=build_start_message_keyboard(settings),
        )

        await bot.pin_chat_message(
            chat_id=settings.bot.chat_id,
            message_id=sent_message.message_id,
            disable_notification=True,
        )

    return router
