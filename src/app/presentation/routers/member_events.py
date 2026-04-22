from time import perf_counter

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
from app.infrastructure.observability import (
    MetricsCollector,
    get_logger,
    log_step,
    trace_handler,
)
from app.presentation.filters import ChatIdFilter
from app.presentation.formatters import (
    describe_admin_rights_changes,
    describe_restricted_rights_changes,
    format_admin_demotion_message,
    format_admin_promotion_message,
    format_admin_rights_changed_message,
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
    logger = get_logger(__name__)

    @router.chat_member(ChatMemberUpdatedFilter(USER_LEFT_TRANSITION))
    @trace_handler
    async def left_user_event(
        event: ChatMemberUpdated,
        bot: Bot,
        clock: Clock,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        metrics.observe_business_event("user_left")
        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_user_left_message(
                user=map_chat_user(event.old_chat_member.user),
                moment=clock.now(),
            ),
        )
        metrics.observe_handler(
            handler="member_events.left_user_event",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )
        log_step(
            logger,
            "user_left_logged",
            handler="member_events.left_user_event",
            subject_user_id=event.old_chat_member.user.id,
        )

    @router.chat_member(ChatMemberUpdatedFilter(USER_KICKED_TRANSITION))
    @trace_handler
    async def admin_kick_user_event(
        event: ChatMemberUpdated,
        bot: Bot,
        clock: Clock,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        metrics.observe_business_event("user_kicked")
        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_user_kicked_message(
                user=map_chat_user(event.new_chat_member.user),
                admin=map_chat_user(event.from_user),
                moment=clock.now(),
            ),
        )
        metrics.observe_handler(
            handler="member_events.admin_kick_user_event",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )
        log_step(
            logger,
            "user_kick_logged",
            handler="member_events.admin_kick_user_event",
            actor_user_id=event.from_user.id,
            subject_user_id=event.new_chat_member.user.id,
        )

    @router.chat_member(ChatMemberUpdatedFilter(USER_JOINED_TRANSITION))
    @trace_handler
    async def on_user_joined(
        event: ChatMemberUpdated,
        bot: Bot,
        clock: Clock,
        metrics: MetricsCollector,
    ) -> None:
        if event.from_user.id != event.new_chat_member.user.id:
            return

        started_at = perf_counter()
        metrics.observe_business_event("user_joined")
        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_user_joined_message(
                user=map_chat_user(event.new_chat_member.user),
                moment=clock.now(),
            ),
        )
        metrics.observe_handler(
            handler="member_events.on_user_joined",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )
        log_step(
            logger,
            "user_join_logged",
            handler="member_events.on_user_joined",
            subject_user_id=event.new_chat_member.user.id,
        )

    @router.chat_member()
    @trace_handler
    async def member_rights_event(
        event: ChatMemberUpdated,
        bot: Bot,
        clock: Clock,
        metrics: MetricsCollector,
    ) -> None:
        old_status = event.old_chat_member.status
        new_status = event.new_chat_member.status

        if new_status == ChatMemberStatus.ADMINISTRATOR:
            started_at = perf_counter()
            promoted_user = map_chat_user(event.new_chat_member.user)

            if old_status != ChatMemberStatus.ADMINISTRATOR:
                rights_text = format_admin_rights(event.new_chat_member)
                metrics.observe_business_event("admin_promoted")

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
                        f"🛡 {promoted_user.mention_html}, тебе выдали права администратора.\n\n"
                        "🔗 Вступи, пожалуйста, в наши служебные чаты по кнопкам ниже.\n"
                        "🔐 Доступ туда открыт только для администрации."
                    ),
                    reply_markup=build_admin_invite_keyboard(settings),
                )
                metrics.observe_handler(
                    handler="member_events.member_rights_event",
                    status="success",
                    duration_seconds=perf_counter() - started_at,
                )
                log_step(
                    logger,
                    "admin_promoted_logged",
                    handler="member_events.member_rights_event",
                    subject_user_id=event.new_chat_member.user.id,
                )
                return

            rights_changes = describe_admin_rights_changes(
                event.old_chat_member,
                event.new_chat_member,
            )
            if rights_changes is None:
                return

            metrics.observe_business_event("admin_rights_changed")
            await bot.send_message(
                chat_id=settings.bot.log_chat_id,
                text=format_admin_rights_changed_message(
                    user=promoted_user,
                    rights_changes=rights_changes,
                    moment=clock.now(),
                ),
            )
            metrics.observe_handler(
                handler="member_events.member_rights_event",
                status="success",
                duration_seconds=perf_counter() - started_at,
            )
            log_step(
                logger,
                "admin_rights_changed_logged",
                handler="member_events.member_rights_event",
                subject_user_id=event.new_chat_member.user.id,
            )
            return

        if old_status == ChatMemberStatus.ADMINISTRATOR:
            if new_status == ChatMemberStatus.RESTRICTED:
                pass
            else:
                started_at = perf_counter()
                metrics.observe_business_event("admin_demoted")
                await bot.send_message(
                    chat_id=settings.bot.log_chat_id,
                    text=format_admin_demotion_message(
                        user=map_chat_user(event.new_chat_member.user),
                        moment=clock.now(),
                    ),
                )
                metrics.observe_handler(
                    handler="member_events.member_rights_event",
                    status="success",
                    duration_seconds=perf_counter() - started_at,
                )
                log_step(
                    logger,
                    "admin_demoted_logged",
                    handler="member_events.member_rights_event",
                    subject_user_id=event.new_chat_member.user.id,
                )
                return

        if (
            old_status != ChatMemberStatus.RESTRICTED
            and new_status != ChatMemberStatus.RESTRICTED
        ):
            return

        change_set = describe_restricted_rights_changes(
            event.old_chat_member,
            event.new_chat_member,
        )
        if change_set is None:
            return

        started_at = perf_counter()
        metrics.observe_business_event("user_restricted")
        await bot.send_message(
            chat_id=settings.bot.log_chat_id,
            text=format_user_restricted_message(
                user=map_chat_user(event.new_chat_member.user),
                change_set=change_set,
                moment=clock.now(),
            ),
        )
        metrics.observe_handler(
            handler="member_events.member_rights_event",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )
        log_step(
            logger,
            "user_restricted_logged",
            handler="member_events.member_rights_event",
            subject_user_id=event.new_chat_member.user.id,
        )

    return router
