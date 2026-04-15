from aiogram import Bot, Router
from aiogram.types import ChatJoinRequest

from app.application.services import AdminAccessService
from app.config import Settings
from app.presentation.filters import ChatIdFilter


def create_join_request_router(settings: Settings) -> Router:
    router = Router(name="join-requests")

    @router.chat_join_request(ChatIdFilter(settings.bot.info_chat_admin_id))
    async def admin_info_join_request(
        request: ChatJoinRequest,
        bot: Bot,
        admin_access_service: AdminAccessService,
    ) -> None:
        if await admin_access_service.is_chat_admin(bot, request.from_user.id):
            await request.approve()
            return

        await request.decline()

    @router.chat_join_request(ChatIdFilter(settings.bot.log_chat_id))
    async def log_chat_join_request(
        request: ChatJoinRequest,
        bot: Bot,
        admin_access_service: AdminAccessService,
    ) -> None:
        if await admin_access_service.is_chat_admin(bot, request.from_user.id):
            await request.approve()
            return

        await request.decline()

    return router
