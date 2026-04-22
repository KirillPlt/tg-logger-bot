from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import Settings
from app.presentation.formatters import build_chat_deep_link


def build_start_message_keyboard(settings: Settings) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Чат",
                    url=build_chat_deep_link(settings.bot.chat_id),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Лог чат",
                    url=settings.bot.log_chat_invite_url,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛡 Инфо-админ",
                    url=settings.bot.info_chat_admin_invite_url,
                )
            ],
        ]
    )


def build_admin_invite_keyboard(settings: Settings) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚙️ Лог чат",
                    url=settings.bot.log_chat_invite_url,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛡 Инфо-админ",
                    url=settings.bot.info_chat_admin_invite_url,
                )
            ],
        ]
    )
