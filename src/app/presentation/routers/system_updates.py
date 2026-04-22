from html import escape
from time import perf_counter
from collections.abc import Sequence

from aiogram import Bot, Router
from aiogram.types import (
    ChatBoostRemoved,
    ChatBoostUpdated,
    ChatMemberUpdated,
    MessageReactionCountUpdated,
    MessageReactionUpdated,
    ReactionTypeCustomEmoji,
    ReactionTypeEmoji,
    ReactionTypePaid,
)

from app.application.protocols import Clock
from app.application.services import BotRuntimeSettingsService
from app.config import Settings
from app.infrastructure.observability import (
    MetricsCollector,
    get_logger,
    log_step,
    trace_handler,
)
from app.presentation.filters import ChatIdFilter
from app.presentation.formatters import format_message_reference


def create_system_update_router(settings: Settings) -> Router:
    router = Router(name="system-updates")
    router.message_reaction.filter(ChatIdFilter(settings.bot.chat_id))
    router.message_reaction_count.filter(ChatIdFilter(settings.bot.chat_id))
    router.chat_boost.filter(ChatIdFilter(settings.bot.chat_id))
    router.removed_chat_boost.filter(ChatIdFilter(settings.bot.chat_id))
    router.my_chat_member.filter(ChatIdFilter(settings.bot.chat_id))
    logger = get_logger(__name__)

    @router.message_reaction()
    @trace_handler
    async def message_reaction_event(
        event: MessageReactionUpdated,
        bot: Bot,
        clock: Clock,
        bot_runtime_settings_service: BotRuntimeSettingsService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        if not await bot_runtime_settings_service.is_reaction_logging_enabled():
            metrics.observe_handler(
                handler="system_updates.message_reaction_event",
                status="disabled",
                duration_seconds=perf_counter() - started_at,
            )
            log_step(
                logger,
                "message_reaction_logging_skipped",
                handler="system_updates.message_reaction_event",
                message_id=event.message_id,
            )
            return

        actor_name = _format_reaction_actor_name(event)
        actor_id_line = (
            f"🆔 Кто поставил реакцию: #id{event.user.id}"
            if event.user is not None
            else "🆔 Кто поставил реакцию: <i>анонимно / actor_chat</i>"
        )
        old_reaction = _render_reactions(event.old_reaction)
        new_reaction = _render_reactions(event.new_reaction)
        actor_id_footer = f"\n#id{event.user.id}" if event.user is not None else ""

        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=(
                f"🕒 <b>{clock.now().strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
                f"😀 Пользователь изменил реакцию.\n\n"
                f"👤 Кто: {actor_name}\n"
                f"{format_message_reference(event.chat.id, event.message_id)}\n"
                f"{actor_id_line}\n"
                f"💬 ID сообщения: {event.message_id}\n\n"
                f"⬅️ Было: {old_reaction}\n"
                f"➡️ Стало: {new_reaction}\n\n"
                f"#ИЗМЕНИЛИ_РЕАКЦИЮ"
                f"{actor_id_footer}"
            ),
        )
        metrics.observe_business_event("message_reaction_updated")
        metrics.observe_handler(
            handler="system_updates.message_reaction_event",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )
        log_step(
            logger,
            "message_reaction_logged",
            handler="system_updates.message_reaction_event",
            message_id=event.message_id,
        )

    @router.message_reaction_count()
    @trace_handler
    async def message_reaction_count_event(
        event: MessageReactionCountUpdated,
        bot: Bot,
        clock: Clock,
        bot_runtime_settings_service: BotRuntimeSettingsService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        if not await bot_runtime_settings_service.is_reaction_logging_enabled():
            metrics.observe_handler(
                handler="system_updates.message_reaction_count_event",
                status="disabled",
                duration_seconds=perf_counter() - started_at,
            )
            log_step(
                logger,
                "message_reaction_count_logging_skipped",
                handler="system_updates.message_reaction_count_event",
                message_id=event.message_id,
            )
            return

        reactions_summary = (
            ", ".join(
                f"{_reaction_type_to_text(reaction.type)} x{reaction.total_count}"
                for reaction in event.reactions
            )
            or "😶 Нет реакций"
        )
        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=(
                f"🕒 <b>{clock.now().strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
                f"📊 <b>Telegram прислал агрегированное обновление реакций.</b>\n"
                f"{format_message_reference(event.chat.id, event.message_id)}\n"
                f"💬 ID сообщения: <code>{event.message_id}</code>\n"
                f"📈 Реакции сейчас: {reactions_summary}\n\n"
                f"<b>#ОБНОВИЛИ_СЧЕТЧИК_РЕАКЦИЙ</b>"
            ),
        )
        metrics.observe_business_event("message_reaction_count_updated")
        metrics.observe_handler(
            handler="system_updates.message_reaction_count_event",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )

    @router.chat_boost()
    @trace_handler
    async def chat_boost_event(
        event: ChatBoostUpdated,
        bot: Bot,
        clock: Clock,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        source = type(event.boost.source).__name__

        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=(
                f"🕒 <b>{clock.now().strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
                f"🚀 <b>Чат получил новый boost.</b>\n"
                f"🆔 Boost ID: <code>{event.boost.boost_id}</code>\n"
                f"📦 Источник: <b>{source}</b>\n\n"
                f"<b>#ПОЛУЧИЛИ_БУСТ</b>"
            ),
        )
        metrics.observe_business_event("chat_boost_added")
        metrics.observe_handler(
            handler="system_updates.chat_boost_event",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )

    @router.removed_chat_boost()
    @trace_handler
    async def removed_chat_boost_event(
        event: ChatBoostRemoved,
        bot: Bot,
        clock: Clock,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        source = type(event.source).__name__

        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=(
                f"🕒 <b>{clock.now().strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
                f"🚀 <b>У чата отозвали boost.</b>\n"
                f"🆔 Boost ID: <code>{event.boost_id}</code>\n"
                f"🗓 Удален: <b>{event.remove_date.strftime('%d.%m.%Y | %H:%M')}</b>\n"
                f"📦 Источник: <b>{source}</b>\n\n"
                f"<b>#УБРАЛИ_БУСТ</b>"
            ),
        )
        metrics.observe_business_event("chat_boost_removed")
        metrics.observe_handler(
            handler="system_updates.removed_chat_boost_event",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )

    @router.my_chat_member()
    @trace_handler
    async def bot_chat_member_event(
        event: ChatMemberUpdated,
        bot: Bot,
        clock: Clock,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=(
                f"🕒 <b>{clock.now().strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
                f"🤖 <b>Изменился статус самого бота в основном чате.</b>\n"
                f"⬅️ Было: <b>{event.old_chat_member.status}</b>\n"
                f"➡️ Стало: <b>{event.new_chat_member.status}</b>\n\n"
                f"<b>#ИЗМЕНИЛСЯ_СТАТУС_БОТА</b>"
            ),
        )
        metrics.observe_business_event("bot_status_changed")
        metrics.observe_handler(
            handler="system_updates.bot_chat_member_event",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )
        log_step(
            logger,
            "bot_status_logged",
            handler="system_updates.bot_chat_member_event",
            old_status=event.old_chat_member.status,
            new_status=event.new_chat_member.status,
        )

    return router


def _render_reactions(
    reactions: Sequence[ReactionTypeEmoji | ReactionTypeCustomEmoji | ReactionTypePaid],
) -> str:
    if not reactions:
        return "😶 Без реакции"

    return ", ".join(_reaction_type_to_text(reaction) for reaction in reactions)


def _reaction_type_to_text(reaction: object) -> str:
    emoji = getattr(reaction, "emoji", None)
    if emoji is not None:
        return str(emoji)

    custom_emoji_id = getattr(reaction, "custom_emoji_id", None)
    if custom_emoji_id is not None:
        return f'<tg-emoji emoji-id="{custom_emoji_id}"></tg-emoji>'

    is_paid = getattr(reaction, "type", None)
    if is_paid == "paid":
        return "⭐"

    return str(reaction)


def _format_reaction_actor_name(event: MessageReactionUpdated) -> str:
    if event.user is not None:
        username_tag = f" [@{event.user.username}]" if event.user.username else ""
        return f"# {escape(event.user.full_name)}{username_tag}"

    if event.actor_chat is not None:
        actor_chat_title = event.actor_chat.title or "Неизвестный чат"
        return f"# {escape(actor_chat_title)}"

    return "Неизвестный источник"
