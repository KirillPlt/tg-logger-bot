from time import perf_counter

from aiogram import Bot, Router
from aiogram.types import ChatJoinRequest

from app.application.services import AdminAccessService
from app.config import Settings
from app.infrastructure.observability import (
    MetricsCollector,
    get_logger,
    log_step,
    trace_handler,
)
from app.presentation.filters import ChatIdFilter


def create_join_request_router(settings: Settings) -> Router:
    router = Router(name="join-requests")
    logger = get_logger(__name__)

    @router.chat_join_request(ChatIdFilter(settings.bot.info_chat_admin_id))
    @trace_handler
    async def admin_info_join_request(
        request: ChatJoinRequest,
        bot: Bot,
        admin_access_service: AdminAccessService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        log_step(
            logger,
            "join_request_received",
            handler="join_requests.admin_info_join_request",
            actor_user_id=request.from_user.id,
            target_chat_id=request.chat.id,
        )
        if await admin_access_service.is_chat_admin(bot, request.from_user.id):
            await request.approve()
            metrics.observe_business_event("join_request_approved")
            metrics.observe_handler(
                handler="join_requests.admin_info_join_request",
                status="approved",
                duration_seconds=perf_counter() - started_at,
            )
            log_step(
                logger,
                "join_request_approved",
                handler="join_requests.admin_info_join_request",
                actor_user_id=request.from_user.id,
            )
            return

        await request.decline()
        metrics.observe_business_event("join_request_declined")
        metrics.observe_handler(
            handler="join_requests.admin_info_join_request",
            status="declined",
            duration_seconds=perf_counter() - started_at,
        )
        log_step(
            logger,
            "join_request_declined",
            handler="join_requests.admin_info_join_request",
            actor_user_id=request.from_user.id,
        )

    @router.chat_join_request(ChatIdFilter(settings.bot.log_chat_id))
    @trace_handler
    async def log_chat_join_request(
        request: ChatJoinRequest,
        bot: Bot,
        admin_access_service: AdminAccessService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        log_step(
            logger,
            "join_request_received",
            handler="join_requests.log_chat_join_request",
            actor_user_id=request.from_user.id,
            target_chat_id=request.chat.id,
        )
        if await admin_access_service.is_chat_admin(bot, request.from_user.id):
            await request.approve()
            metrics.observe_business_event("join_request_approved")
            metrics.observe_handler(
                handler="join_requests.log_chat_join_request",
                status="approved",
                duration_seconds=perf_counter() - started_at,
            )
            log_step(
                logger,
                "join_request_approved",
                handler="join_requests.log_chat_join_request",
                actor_user_id=request.from_user.id,
            )
            return

        await request.decline()
        metrics.observe_business_event("join_request_declined")
        metrics.observe_handler(
            handler="join_requests.log_chat_join_request",
            status="declined",
            duration_seconds=perf_counter() - started_at,
        )
        log_step(
            logger,
            "join_request_declined",
            handler="join_requests.log_chat_join_request",
            actor_user_id=request.from_user.id,
        )

    return router
