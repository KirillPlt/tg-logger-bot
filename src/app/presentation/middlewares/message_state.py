from __future__ import annotations

from collections.abc import Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, TelegramObject

from app.application.services import ChatStateService, MessageSnapshotService
from app.config import Settings
from app.infrastructure.observability import get_logger, log_step
from app.presentation.formatters import (
    describe_service_message,
    get_renderable_message_html,
)


class MessageStateMiddleware(BaseMiddleware):
    def __init__(
        self,
        settings: Settings,
        message_snapshot_service: MessageSnapshotService,
        chat_state_service: ChatStateService,
    ) -> None:
        self._settings = settings
        self._message_snapshot_service = message_snapshot_service
        self._chat_state_service = chat_state_service
        self._logger = get_logger(__name__)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, object]], Awaitable[object]],
        event: TelegramObject,
        data: dict[str, object],
    ) -> object:
        if not isinstance(event, Message):
            return await handler(event, data)

        if event.chat.id != self._settings.bot.chat_id:
            return await handler(event, data)

        if event.edit_date is not None:
            data[
                "previous_message_snapshot"
            ] = await self._message_snapshot_service.get(
                event.chat.id,
                event.message_id,
            )

        result = await handler(event, data)

        renderable_html = get_renderable_message_html(event)
        await self._message_snapshot_service.save(
            chat_id=event.chat.id,
            message_id=event.message_id,
            content_type=str(event.content_type),
            rendered_html=renderable_html,
        )

        bot = data.get("bot")
        if isinstance(bot, Bot):
            service_message = await describe_service_message(
                message=event,
                chat_state_service=self._chat_state_service,
            )
            if service_message is not None:
                await bot.send_message(
                    chat_id=self._settings.bot.log_chat_id,
                    text=service_message,
                )
                log_step(
                    self._logger,
                    "system_message_logged",
                    message_id=event.message_id,
                    content_type=str(event.content_type),
                )

        return result
