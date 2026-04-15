from aiogram import Bot, Router
from aiogram.enums import ChatMemberStatus
from aiogram.filters import (
    IS_MEMBER,
    KICKED,
    LEFT,
    RESTRICTED,
    ChatMemberUpdatedFilter,
)
from aiogram.types import ChatMemberUpdated

from app.application.protocols import Clock
from app.config import Settings
from app.presentation.filters import ChatIdFilter
from app.presentation.formatters import (
    describe_restricted_rights_changes,
    format_admin_promotion_message,
    format_admin_rights,
    format_user_joined_message,
    format_user_kicked_message,
    format_user_left_message,
    format_user_restricted_message,
)
from app.presentation.keyboards import build_admin_invite_keyboard
from app.presentation.mappers import map_chat_user


USER_KICKED_TRANSITION = IS_MEMBER >> (KICKED | -RESTRICTED)
USER_LEFT_TRANSITION = IS_MEMBER >> LEFT
USER_JOINED_TRANSITION = (KICKED | LEFT) >> IS_MEMBER


def create_member_event_router(settings: Settings) -> Router:
    router = Router(name="member-events")
    router.chat_member.filter(ChatIdFilter(settings.bot.chat_id))

    @router.chat_member(ChatMemberUpdatedFilter(USER_LEFT_TRANSITION))
    async def left_user_event(event: ChatMemberUpdated, bot: Bot, clock: Clock) -> None:
        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_user_left_message(
                user=map_chat_user(event.old_chat_member.user),
                moment=clock.now(),
            ),
        )

    @router.chat_member(ChatMemberUpdatedFilter(USER_KICKED_TRANSITION))
    async def admin_kick_user_event(event: ChatMemberUpdated, bot: Bot, clock: Clock) -> None:
        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_user_kicked_message(
                user=map_chat_user(event.new_chat_member.user),
                admin=map_chat_user(event.from_user),
                moment=clock.now(),
            ),
        )

    @router.chat_member(ChatMemberUpdatedFilter(USER_JOINED_TRANSITION))
    async def on_user_joined(event: ChatMemberUpdated, bot: Bot, clock: Clock) -> None:
        if event.from_user.id != event.new_chat_member.user.id:
            return

        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_user_joined_message(
                user=map_chat_user(event.new_chat_member.user),
                moment=clock.now(),
            ),
        )

    @router.chat_member()
    async def restricted_user_event(event: ChatMemberUpdated, bot: Bot, clock: Clock) -> None:
        if (
            event.old_chat_member.status != ChatMemberStatus.RESTRICTED
            and event.new_chat_member.status != ChatMemberStatus.RESTRICTED
        ):
            return

        change_set = describe_restricted_rights_changes(
            event.old_chat_member,
            event.new_chat_member,
        )
        if change_set is None:
            return

        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_user_restricted_message(
                user=map_chat_user(event.new_chat_member.user),
                change_set=change_set,
                moment=clock.now(),
            ),
        )

    @router.chat_member()
    async def admin_promoted_event(event: ChatMemberUpdated, bot: Bot, clock: Clock) -> None:
        if (
            event.old_chat_member.status == ChatMemberStatus.ADMINISTRATOR
            or event.new_chat_member.status != ChatMemberStatus.ADMINISTRATOR
        ):
            return

        promoted_user = map_chat_user(event.new_chat_member.user)
        rights_text = format_admin_rights(event.new_chat_member)

        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_admin_promotion_message(
                user=promoted_user,
                rights_text=rights_text,
                moment=clock.now(),
            ),
        )

        await bot.send_message(
            chat_id=settings.bot.chat_id,
            text=(
                f"✉️ {promoted_user.mention_html}, так как тебя назначили администратором, "
                "просим тебя вступить в наши служебные чаты, доступные только администрации."
            ),
            reply_markup=build_admin_invite_keyboard(settings),
        )

    return router
