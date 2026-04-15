from aiogram import Bot, F, Router
from aiogram.types import Message

from app.application.protocols import Clock
from app.config import Settings
from app.presentation.filters import ChatIdFilter
from app.presentation.formatters import (
    describe_edited_message_content,
    extract_edited_message_payload,
    format_edited_message_notice,
    format_user_added_message,
)
from app.presentation.mappers import map_chat_user, map_chat_users


def create_message_event_router(settings: Settings) -> Router:
    router = Router(name="message-events")
    router.message.filter(ChatIdFilter(settings.bot.chat_id))
    router.edited_message.filter(ChatIdFilter(settings.bot.chat_id))

    @router.message(F.new_chat_members)
    async def user_add_user_event(message: Message, bot: Bot, clock: Clock) -> None:
        if message.from_user is None or not message.new_chat_members:
            return

        if len(message.new_chat_members) == 1 and message.from_user.id == message.new_chat_members[0].id:
            return

        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_user_added_message(
                adder=map_chat_user(message.from_user),
                added_users=map_chat_users(message.new_chat_members),
                moment=clock.now(),
            ),
        )

    @router.edited_message()
    async def edit_message_event(message: Message, bot: Bot, clock: Clock) -> None:
        if message.from_user is None:
            return

        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_edited_message_notice(
                user=map_chat_user(message.from_user),
                content_description=describe_edited_message_content(message),
                moment=clock.now(),
            ),
        )

        payload = extract_edited_message_payload(message)
        if payload is None:
            return

        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=payload,
        )

    return router
