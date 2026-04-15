from time import perf_counter

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import Settings
from app.infrastructure.observability import MetricsCollector, get_logger, log_step
from app.presentation.filters import ChatIdFilter, OwnerFilter
from app.presentation.keyboards import build_start_message_keyboard


START_MESSAGE_TEXT = (
    "📌 <b>Служебные чаты администрации</b>\n\n"
    "Чтобы удобно получать отчеты и служебную информацию по группе, "
    "вступите в наши внутренние чаты через кнопки ниже.\n\n"
    "🔐 <b>Доступ в лог-чат</b> открыт только администрации.\n"
    "🚫 Посторонних пользователей бот автоматически не пропустит.\n"
    "ℹ️ <b>Инфо-чат</b> тоже доступен только администраторам.\n\n"
    "Выберите нужный чат:"
)


def create_start_router(settings: Settings) -> Router:
    router = Router(name="start")
    router.message.filter(ChatIdFilter(settings.bot.chat_id))
    logger = get_logger(__name__)

    @router.message(Command("start"), OwnerFilter(settings.bot.owner_id))
    async def start_handler(message: Message, bot: Bot, metrics: MetricsCollector) -> None:
        started_at = perf_counter()
        log_step(
            logger,
            "start_command_received",
            handler="start.start_handler",
            actor_user_id=message.from_user.id if message.from_user is not None else None,
        )
        sent_message = await message.answer(
            text=START_MESSAGE_TEXT,
            reply_markup=build_start_message_keyboard(settings),
        )
        metrics.observe_telegram_action(
            action="send_start_message",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )

        await bot.pin_chat_message(
            chat_id=settings.bot.chat_id,
            message_id=sent_message.message_id,
            disable_notification=True,
        )
        metrics.observe_business_event("start_command")
        metrics.observe_telegram_action(
            action="pin_start_message",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )
        metrics.observe_handler(
            handler="start.start_handler",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )
        log_step(
            logger,
            "start_message_pinned",
            handler="start.start_handler",
            message_id=sent_message.message_id,
        )

    return router
