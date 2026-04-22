from time import perf_counter

from aiogram import Bot, F, Router
from aiogram.types import Message

from app.application.protocols import Clock
from app.config import Settings
from app.domain.models import MessageSnapshot
from app.infrastructure.observability import (
    MetricsCollector,
    get_logger,
    log_step,
    trace_handler,
)
from app.presentation.filters import ChatIdFilter
from app.presentation.formatters import (
    describe_edited_message_content,
    format_message_reference,
    format_edited_message_diff,
    format_user_added_message,
    get_renderable_message_html,
)
from app.presentation.mappers import map_chat_user, map_chat_users


def create_message_event_router(settings: Settings) -> Router:
    router = Router(name="message-events")
    router.message.filter(ChatIdFilter(settings.bot.chat_id))
    router.edited_message.filter(ChatIdFilter(settings.bot.chat_id))
    logger = get_logger(__name__)

    @router.message(F.new_chat_members)
    @trace_handler
    async def user_add_user_event(
        message: Message,
        bot: Bot,
        clock: Clock,
        metrics: MetricsCollector,
    ) -> None:
        if message.from_user is None or not message.new_chat_members:
            return

        if (
            len(message.new_chat_members) == 1
            and message.from_user.id == message.new_chat_members[0].id
        ):
            return

        started_at = perf_counter()
        metrics.observe_business_event("user_added")
        log_step(
            logger,
            "user_add_event_detected",
            handler="message_events.user_add_user_event",
            actor_user_id=message.from_user.id,
            added_user_ids=[user.id for user in message.new_chat_members],
        )
        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_user_added_message(
                adder=map_chat_user(message.from_user),
                added_users=map_chat_users(message.new_chat_members),
                moment=clock.now(),
                message_reference=format_message_reference(
                    message.chat.id, message.message_id
                ),
            ),
        )
        metrics.observe_telegram_action(
            action="send_user_added_log",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )
        metrics.observe_handler(
            handler="message_events.user_add_user_event",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )

    @router.edited_message()
    @trace_handler
    async def edit_message_event(
        message: Message,
        bot: Bot,
        clock: Clock,
        previous_message_snapshot: MessageSnapshot | None,
        metrics: MetricsCollector,
    ) -> None:
        if message.from_user is None:
            return

        started_at = perf_counter()
        current_payload = get_renderable_message_html(message)
        text: str | None = format_edited_message_diff(
            user=map_chat_user(message.from_user),
            content_description=describe_edited_message_content(message),
            previous_snapshot=previous_message_snapshot,
            current_payload=current_payload,
            moment=clock.now(),
            message_reference=format_message_reference(
                message.chat.id, message.message_id
            ),
        )
        if text:
            metrics.observe_business_event("message_edited")
            log_step(
                logger,
                "edited_message_detected",
                handler="message_events.edit_message_event",
                actor_user_id=message.from_user.id,
                message_id=message.message_id,
                previous_snapshot_exists=previous_message_snapshot is not None,
            )
            await bot.send_message(
                chat_id=settings.bot.log_chat_id,
                text=text,
            )
            metrics.observe_telegram_action(
                action="send_edited_message_log",
                status="success",
                duration_seconds=perf_counter() - started_at,
            )
            metrics.observe_handler(
                handler="message_events.edit_message_event",
                status="success",
                duration_seconds=perf_counter() - started_at,
            )

    return router
