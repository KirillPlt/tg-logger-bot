from __future__ import annotations

from html import escape
from time import perf_counter
from typing import Any, cast

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message

from app.application.services import (
    AdminAccessService,
    BotRuntimeSettingsService,
    CustomCommandService,
    NoteService,
)
from app.application.services.pending_text_updates import (
    PendingTextUpdate,
    PendingTextUpdateStore,
    TextEntityKind,
)
from app.application.services.smart_text_lookup import (
    SearchableTextEntry,
    SmartTextLookupService,
    canonicalize_saved_text_trigger,
)
from app.config import Settings
from app.domain.models import CustomCommand, SavedNote, normalize_command_name
from app.infrastructure.observability import (
    MetricsCollector,
    get_logger,
    log_step,
    trace_handler,
)
from app.presentation.filters import OwnerFilter
from app.presentation.keyboards import build_text_update_confirmation_keyboard
from app.presentation.parsers import (
    CREATE_GREETING_PREFIX,
    CREATE_NOTE_PREFIX,
    LIST_COMMANDS_REQUEST,
    parse_create_command,
    parse_create_greeting,
    parse_create_note,
    parse_delete_command,
)


ALLOWED_CHAT_TYPES = {ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP}
GREETING_TRIGGER = "приветствие"
TEXT_UPDATE_PREFIX = "text_update:"
MAX_TELEGRAM_MESSAGE_LENGTH = 4096

CREATE_COMMAND_USAGE_TEXT = (
    "🛠 <b>Создание кастомной команды</b>\n\n"
    "Первая строка:\n"
    "<code>+команда имя команды</code>\n\n"
    "Со второй строки:\n"
    "многострочный текст ответа"
)
CREATE_GREETING_USAGE_TEXT = (
    "👋 <b>Сохранение приветствия</b>\n\n"
    "Первая строка:\n"
    f"<code>{CREATE_GREETING_PREFIX}</code>\n\n"
    "Со второй строки:\n"
    "многострочный текст приветствия"
)
CREATE_NOTE_USAGE_TEXT = (
    "🗒 <b>Сохранение заметки</b>\n\n"
    "Первая строка:\n"
    f"<code>{CREATE_NOTE_PREFIX} название</code>\n\n"
    "Со второй строки:\n"
    "многострочный текст заметки"
)
DELETE_USAGE_TEXT = (
    "🗑 <b>Удаление кастомной команды</b>\n\n"
    "Используй формат:\n"
    "<code>-команда имя команды</code>"
)


def create_custom_command_router(settings: Settings) -> Router:
    router = Router(name="custom-commands")
    owner_filter = OwnerFilter(settings.bot.owner_id)
    logger = get_logger(__name__)
    pending_updates = PendingTextUpdateStore()
    smart_lookup = SmartTextLookupService()

    @router.message(
        F.text.startswith(CREATE_GREETING_PREFIX),
        owner_filter,
        F.chat.type.in_(ALLOWED_CHAT_TYPES),
    )
    @trace_handler
    async def set_greeting_handler(
        message: Message,
        bot_runtime_settings_service: BotRuntimeSettingsService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        actor_user_id = message.from_user.id if message.from_user is not None else None
        log_step(
            logger,
            "greeting_save_requested",
            handler="custom_commands.set_greeting_handler",
            actor_user_id=actor_user_id,
        )

        parsed_greeting = parse_create_greeting(message.text, message.html_text)
        if parsed_greeting is None:
            await message.answer(CREATE_GREETING_USAGE_TEXT)
            metrics.observe_handler(
                handler="custom_commands.set_greeting_handler",
                status="invalid_input",
                duration_seconds=perf_counter() - started_at,
            )
            return

        current_greeting = await bot_runtime_settings_service.get_greeting()
        if current_greeting is None:
            try:
                _, was_changed = await bot_runtime_settings_service.set_greeting(
                    parsed_greeting.response_html
                )
            except ValueError as error:
                await message.answer(
                    _format_save_failed_message("приветствие", None, str(error))
                )
                metrics.observe_handler(
                    handler="custom_commands.set_greeting_handler",
                    status="validation_error",
                    duration_seconds=perf_counter() - started_at,
                )
                return

            await message.answer(
                _format_saved_message(
                    entity_kind="greeting",
                    display_name=None,
                    was_created=True,
                    changed=was_changed,
                )
            )
            metrics.observe_handler(
                handler="custom_commands.set_greeting_handler",
                status="created",
                duration_seconds=perf_counter() - started_at,
            )
            return

        if actor_user_id is None:
            await message.answer(
                _format_save_failed_message(
                    "приветствие",
                    None,
                    "Не удалось определить автора команды.",
                )
            )
            metrics.observe_handler(
                handler="custom_commands.set_greeting_handler",
                status="actor_missing",
                duration_seconds=perf_counter() - started_at,
            )
            return

        pending = pending_updates.create(
            requester_user_id=actor_user_id,
            entity_kind="greeting",
            display_name=None,
            target_key=None,
            proposed_html=parsed_greeting.response_html.strip(),
        )
        await message.answer(
            _format_confirmation_preview(
                entity_kind="greeting",
                display_name=None,
                current_html=current_greeting,
                new_html=parsed_greeting.response_html.strip(),
            ),
            reply_markup=build_text_update_confirmation_keyboard(pending.token),
        )
        metrics.observe_handler(
            handler="custom_commands.set_greeting_handler",
            status="confirmation_requested",
            duration_seconds=perf_counter() - started_at,
        )

    @router.message(
        F.text.startswith(CREATE_NOTE_PREFIX),
        owner_filter,
        F.chat.type.in_(ALLOWED_CHAT_TYPES),
    )
    @trace_handler
    async def set_note_handler(
        message: Message,
        note_service: NoteService,
        custom_command_service: CustomCommandService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        actor_user_id = message.from_user.id if message.from_user is not None else None
        parsed_note = parse_create_note(message.text, message.html_text)
        if parsed_note is None:
            await message.answer(CREATE_NOTE_USAGE_TEXT)
            metrics.observe_handler(
                handler="custom_commands.set_note_handler",
                status="invalid_input",
                duration_seconds=perf_counter() - started_at,
            )
            return

        try:
            normalized_name = await _validate_note_name(
                parsed_note.name,
                custom_command_service,
            )
        except ValueError as error:
            await message.answer(
                _format_save_failed_message("заметку", parsed_note.name, str(error))
            )
            metrics.observe_handler(
                handler="custom_commands.set_note_handler",
                status="validation_error",
                duration_seconds=perf_counter() - started_at,
            )
            return

        current_note = await note_service.resolve(parsed_note.name)
        if current_note is None:
            result = await note_service.save(
                parsed_note.name, parsed_note.response_html
            )
            await message.answer(
                _format_saved_message(
                    entity_kind="note",
                    display_name=result.note.display_name,
                    was_created=result.was_created,
                    changed=True,
                )
            )
            metrics.observe_handler(
                handler="custom_commands.set_note_handler",
                status="created",
                duration_seconds=perf_counter() - started_at,
            )
            return

        if actor_user_id is None:
            await message.answer(
                _format_save_failed_message(
                    "заметку",
                    parsed_note.name,
                    "Не удалось определить автора команды.",
                )
            )
            metrics.observe_handler(
                handler="custom_commands.set_note_handler",
                status="actor_missing",
                duration_seconds=perf_counter() - started_at,
            )
            return

        pending = pending_updates.create(
            requester_user_id=actor_user_id,
            entity_kind="note",
            display_name=current_note.display_name,
            target_key=normalized_name,
            proposed_html=parsed_note.response_html.strip(),
        )
        await message.answer(
            _format_confirmation_preview(
                entity_kind="note",
                display_name=current_note.display_name,
                current_html=current_note.response_html,
                new_html=parsed_note.response_html.strip(),
            ),
            reply_markup=build_text_update_confirmation_keyboard(pending.token),
        )
        metrics.observe_handler(
            handler="custom_commands.set_note_handler",
            status="confirmation_requested",
            duration_seconds=perf_counter() - started_at,
        )

    @router.message(
        F.text.startswith("+команда"),
        owner_filter,
        F.chat.type.in_(ALLOWED_CHAT_TYPES),
    )
    @trace_handler
    async def set_custom_command_handler(
        message: Message,
        custom_command_service: CustomCommandService,
        note_service: NoteService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        actor_user_id = message.from_user.id if message.from_user is not None else None
        log_step(
            logger,
            "custom_command_save_requested",
            handler="custom_commands.set_custom_command_handler",
            actor_user_id=actor_user_id,
        )

        parsed_command = parse_create_command(message.text, message.html_text)
        if parsed_command is None:
            await message.answer(CREATE_COMMAND_USAGE_TEXT)
            metrics.observe_handler(
                handler="custom_commands.set_custom_command_handler",
                status="invalid_input",
                duration_seconds=perf_counter() - started_at,
            )
            return

        try:
            normalized_name = await _validate_custom_command_name(
                parsed_command.name,
                note_service,
            )
        except ValueError as error:
            await message.answer(
                _format_save_failed_message("команду", parsed_command.name, str(error))
            )
            metrics.observe_handler(
                handler="custom_commands.set_custom_command_handler",
                status="validation_error",
                duration_seconds=perf_counter() - started_at,
            )
            return

        current_command = await custom_command_service.resolve(parsed_command.name)
        if current_command is None:
            try:
                result = await custom_command_service.save(
                    parsed_command.name,
                    parsed_command.response_html,
                )
            except ValueError as error:
                await message.answer(
                    _format_save_failed_message(
                        "команду", parsed_command.name, str(error)
                    )
                )
                metrics.observe_handler(
                    handler="custom_commands.set_custom_command_handler",
                    status="validation_error",
                    duration_seconds=perf_counter() - started_at,
                )
                return

            await message.answer(
                _format_saved_message(
                    entity_kind="custom_command",
                    display_name=result.command.display_name,
                    was_created=result.was_created,
                    changed=True,
                )
            )
            metrics.observe_handler(
                handler="custom_commands.set_custom_command_handler",
                status="created",
                duration_seconds=perf_counter() - started_at,
            )
            return

        if actor_user_id is None:
            await message.answer(
                _format_save_failed_message(
                    "команду",
                    parsed_command.name,
                    "Не удалось определить автора команды.",
                )
            )
            metrics.observe_handler(
                handler="custom_commands.set_custom_command_handler",
                status="actor_missing",
                duration_seconds=perf_counter() - started_at,
            )
            return

        pending = pending_updates.create(
            requester_user_id=actor_user_id,
            entity_kind="custom_command",
            display_name=current_command.display_name,
            target_key=normalized_name,
            proposed_html=parsed_command.response_html.strip(),
        )
        await message.answer(
            _format_confirmation_preview(
                entity_kind="custom_command",
                display_name=current_command.display_name,
                current_html=current_command.response_html,
                new_html=parsed_command.response_html.strip(),
            ),
            reply_markup=build_text_update_confirmation_keyboard(pending.token),
        )
        metrics.observe_handler(
            handler="custom_commands.set_custom_command_handler",
            status="confirmation_requested",
            duration_seconds=perf_counter() - started_at,
        )

    @router.message(
        F.text == LIST_COMMANDS_REQUEST,
        owner_filter,
        F.chat.type.in_(ALLOWED_CHAT_TYPES),
    )
    @trace_handler
    async def list_custom_commands_handler(
        message: Message,
        custom_command_service: CustomCommandService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        commands = await custom_command_service.list_commands()
        if not commands:
            await message.answer(
                "📭 <b>Список кастомных команд пуст.</b>\n\n"
                "Пока что здесь нет ни одной сохраненной команды."
            )
            metrics.observe_handler(
                handler="custom_commands.list_custom_commands_handler",
                status="empty",
                duration_seconds=perf_counter() - started_at,
            )
            return

        commands_text = "\n".join(
            f"{index}. <code>{escape(command.display_name)}</code>"
            for index, command in enumerate(commands, start=1)
        )
        await message.answer(
            f"📚 <b>Доступные кастомные команды</b>\n\n{commands_text}"
        )
        metrics.observe_handler(
            handler="custom_commands.list_custom_commands_handler",
            status="success",
            duration_seconds=perf_counter() - started_at,
        )

    @router.message(
        F.text.startswith("-команда"), owner_filter, F.chat.type.in_(ALLOWED_CHAT_TYPES)
    )
    @trace_handler
    async def delete_custom_command_handler(
        message: Message,
        custom_command_service: CustomCommandService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        command_name = parse_delete_command(message.text)
        if command_name is None:
            await message.answer(DELETE_USAGE_TEXT)
            metrics.observe_handler(
                handler="custom_commands.delete_custom_command_handler",
                status="invalid_input",
                duration_seconds=perf_counter() - started_at,
            )
            return

        try:
            is_deleted = await custom_command_service.delete(command_name)
        except ValueError as error:
            await message.answer(f"❌ <b>Не удалось удалить команду.</b>\n\n{error}")
            metrics.observe_handler(
                handler="custom_commands.delete_custom_command_handler",
                status="validation_error",
                duration_seconds=perf_counter() - started_at,
            )
            return

        if is_deleted:
            await message.answer(
                "✅ <b>Команда удалена.</b>\n\n"
                f"🧩 Имя: <code>{escape(command_name)}</code>"
            )
            metrics.observe_handler(
                handler="custom_commands.delete_custom_command_handler",
                status="success",
                duration_seconds=perf_counter() - started_at,
            )
            return

        await message.answer(
            "❌ <b>Команда не найдена.</b>\n\n"
            f"🧩 Имя: <code>{escape(command_name)}</code>"
        )
        metrics.observe_handler(
            handler="custom_commands.delete_custom_command_handler",
            status="not_found",
            duration_seconds=perf_counter() - started_at,
        )

    @router.callback_query(F.data.startswith(TEXT_UPDATE_PREFIX))
    @trace_handler
    async def process_text_update_callback(
        callback: CallbackQuery,
        custom_command_service: CustomCommandService,
        note_service: NoteService,
        bot_runtime_settings_service: BotRuntimeSettingsService,
        metrics: MetricsCollector,
    ) -> None:
        started_at = perf_counter()
        action, token = _parse_text_update_callback_data(callback.data)
        if action is None or token is None:
            await callback.answer("Не удалось распознать действие.", show_alert=True)
            metrics.observe_handler(
                handler="custom_commands.process_text_update_callback",
                status="invalid_callback",
                duration_seconds=perf_counter() - started_at,
            )
            return

        pending = pending_updates.get(token)
        if pending is None or callback.message is None:
            await callback.answer("Подтверждение уже устарело.", show_alert=True)
            if callback.message is not None:
                await cast(Any, callback.message).edit_text(
                    _format_confirmation_failure_message(
                        None,
                        None,
                        "Подтверждение устарело или бот уже перезапускался.",
                    )
                )
            metrics.observe_handler(
                handler="custom_commands.process_text_update_callback",
                status="stale",
                duration_seconds=perf_counter() - started_at,
            )
            return

        actor_user_id = (
            callback.from_user.id if callback.from_user is not None else None
        )
        if actor_user_id != pending.requester_user_id:
            await callback.answer(
                "Подтвердить изменение может только тот, кто его запросил.",
                show_alert=True,
            )
            metrics.observe_handler(
                handler="custom_commands.process_text_update_callback",
                status="forbidden",
                duration_seconds=perf_counter() - started_at,
            )
            return

        if action == "reject":
            pending_updates.remove(token)
            await cast(Any, callback.message).edit_text(
                _format_confirmation_cancelled_message(
                    pending.entity_kind,
                    pending.display_name,
                )
            )
            await callback.answer("Изменение отменено.")
            metrics.observe_handler(
                handler="custom_commands.process_text_update_callback",
                status="rejected",
                duration_seconds=perf_counter() - started_at,
            )
            return

        pending_updates.remove(token)
        try:
            changed = await _apply_pending_text_update(
                pending,
                note_service=note_service,
                custom_command_service=custom_command_service,
                bot_runtime_settings_service=bot_runtime_settings_service,
            )
        except ValueError as error:
            await cast(Any, callback.message).edit_text(
                _format_confirmation_failure_message(
                    pending.entity_kind,
                    pending.display_name,
                    str(error),
                )
            )
            await callback.answer("Не удалось применить изменение.", show_alert=True)
            metrics.observe_handler(
                handler="custom_commands.process_text_update_callback",
                status="validation_error",
                duration_seconds=perf_counter() - started_at,
            )
            return
        except Exception:
            await cast(Any, callback.message).edit_text(
                _format_confirmation_failure_message(
                    pending.entity_kind,
                    pending.display_name,
                    "Попробуй ещё раз немного позже.",
                )
            )
            await callback.answer(
                "Во время сохранения произошла ошибка.", show_alert=True
            )
            metrics.observe_handler(
                handler="custom_commands.process_text_update_callback",
                status="error",
                duration_seconds=perf_counter() - started_at,
            )
            raise

        await cast(Any, callback.message).edit_text(
            _format_saved_message(
                entity_kind=pending.entity_kind,
                display_name=pending.display_name,
                was_created=False,
                changed=changed,
            )
        )
        await callback.answer("Изменение сохранено.")
        metrics.observe_handler(
            handler="custom_commands.process_text_update_callback",
            status="accepted",
            duration_seconds=perf_counter() - started_at,
        )

    @router.message(F.text, F.chat.type.in_(ALLOWED_CHAT_TYPES))
    @trace_handler
    async def respond_saved_text_handler(
        message: Message,
        bot: Bot,
        custom_command_service: CustomCommandService,
        note_service: NoteService,
        admin_access_service: AdminAccessService,
        bot_runtime_settings_service: BotRuntimeSettingsService,
        metrics: MetricsCollector,
    ) -> None:
        if message.text is None:
            return

        started_at = perf_counter()
        actor_user_id = message.from_user.id if message.from_user is not None else None
        can_access_protected_texts = await _can_access_protected_texts(
            message,
            bot,
            admin_access_service,
            settings.bot.owner_id,
        )

        greeting = await _resolve_exact_greeting(
            message.text,
            bot_runtime_settings_service,
            can_access_protected_texts,
        )
        if greeting is not None:
            await message.answer(greeting)
            metrics.observe_handler(
                handler="custom_commands.respond_saved_text_handler",
                status="greeting_hit",
                duration_seconds=perf_counter() - started_at,
            )
            return

        note = await _resolve_exact_note(
            message.text,
            note_service,
            can_access_protected_texts,
        )
        if note is not None:
            await message.answer(note.response_html)
            metrics.observe_handler(
                handler="custom_commands.respond_saved_text_handler",
                status="note_hit",
                duration_seconds=perf_counter() - started_at,
            )
            return

        command = await _resolve_exact_custom_command(
            message.text,
            custom_command_service,
        )
        if command is not None:
            await message.answer(command.response_html)
            metrics.observe_handler(
                handler="custom_commands.respond_saved_text_handler",
                status="command_hit",
                duration_seconds=perf_counter() - started_at,
            )
            return

        smart_matches = await _find_smart_matches(
            message.text,
            custom_command_service=custom_command_service,
            note_service=note_service,
            bot_runtime_settings_service=bot_runtime_settings_service,
            smart_lookup=smart_lookup,
            can_access_protected_texts=can_access_protected_texts,
        )
        if not smart_matches:
            log_step(
                logger,
                "saved_text_miss",
                handler="custom_commands.respond_saved_text_handler",
                actor_user_id=actor_user_id,
            )
            metrics.observe_handler(
                handler="custom_commands.respond_saved_text_handler",
                status="miss",
                duration_seconds=perf_counter() - started_at,
            )
            return

        for response_text in _build_smart_search_messages(smart_matches):
            await message.answer(response_text)

        log_step(
            logger,
            "saved_text_smart_match",
            handler="custom_commands.respond_saved_text_handler",
            actor_user_id=actor_user_id,
            match_count=len(smart_matches),
        )
        metrics.observe_handler(
            handler="custom_commands.respond_saved_text_handler",
            status="smart_hit",
            duration_seconds=perf_counter() - started_at,
        )

    return router


async def _can_access_protected_texts(
    message: Message,
    bot: Bot,
    admin_access_service: AdminAccessService,
    owner_id: int,
) -> bool:
    if message.from_user is None:
        return False

    if message.from_user.id == owner_id:
        return True

    return await admin_access_service.is_chat_admin(bot, message.from_user.id)


async def _validate_custom_command_name(
    raw_name: str,
    note_service: NoteService,
) -> str:
    normalized_name = normalize_command_name(raw_name)
    if normalized_name == GREETING_TRIGGER:
        raise ValueError("Имя команды <code>приветствие</code> зарезервировано.")

    conflicting_note = await note_service.resolve(raw_name)
    if conflicting_note is not None:
        raise ValueError(
            "Такое имя уже занято заметкой. Используй другое название или обнови заметку."
        )

    return normalized_name


async def _validate_note_name(
    raw_name: str,
    custom_command_service: CustomCommandService,
) -> str:
    normalized_name = normalize_command_name(raw_name)
    if normalized_name == GREETING_TRIGGER:
        raise ValueError("Имя заметки <code>приветствие</code> зарезервировано.")

    conflicting_command = await custom_command_service.resolve(raw_name)
    if conflicting_command is not None:
        raise ValueError(
            "Такое имя уже занято кастомной командой. Используй другое название или обнови команду."
        )

    return normalized_name


async def _apply_pending_text_update(
    pending: PendingTextUpdate,
    *,
    note_service: NoteService,
    custom_command_service: CustomCommandService,
    bot_runtime_settings_service: BotRuntimeSettingsService,
) -> bool:
    if pending.entity_kind == "greeting":
        _, was_changed = await bot_runtime_settings_service.set_greeting(
            pending.proposed_html
        )
        return was_changed

    if pending.display_name is None:
        raise ValueError("Не удалось определить имя сохраняемой сущности.")

    if pending.entity_kind == "note":
        await _validate_note_name(pending.display_name, custom_command_service)
        current_note = await note_service.resolve(pending.display_name)
        was_changed = (
            current_note is None or current_note.response_html != pending.proposed_html
        )
        await note_service.save(pending.display_name, pending.proposed_html)
        return was_changed

    await _validate_custom_command_name(pending.display_name, note_service)
    current_command = await custom_command_service.resolve(pending.display_name)
    was_changed = (
        current_command is None
        or current_command.response_html != pending.proposed_html
    )
    await custom_command_service.save(pending.display_name, pending.proposed_html)
    return was_changed


async def _resolve_exact_greeting(
    raw_text: str,
    bot_runtime_settings_service: BotRuntimeSettingsService,
    can_access_protected_texts: bool,
) -> str | None:
    if not can_access_protected_texts:
        return None

    if canonicalize_saved_text_trigger(raw_text) != canonicalize_saved_text_trigger(
        GREETING_TRIGGER
    ):
        return None

    return await bot_runtime_settings_service.get_greeting()


async def _resolve_exact_note(
    raw_text: str,
    note_service: NoteService,
    can_access_protected_texts: bool,
) -> SavedNote | None:
    if not can_access_protected_texts:
        return None

    try:
        literal_match = await note_service.resolve(raw_text)
    except ValueError:
        literal_match = None

    if literal_match is not None:
        return literal_match

    lookup_key = canonicalize_saved_text_trigger(raw_text)
    if not lookup_key:
        return None

    for note in await note_service.list_notes():
        if canonicalize_saved_text_trigger(note.display_name) == lookup_key:
            return note

    return None


async def _resolve_exact_custom_command(
    raw_text: str,
    custom_command_service: CustomCommandService,
) -> CustomCommand | None:
    try:
        literal_match = await custom_command_service.resolve(raw_text)
    except ValueError:
        literal_match = None

    if literal_match is not None:
        return literal_match

    lookup_key = canonicalize_saved_text_trigger(raw_text)
    if not lookup_key:
        return None

    for command in await custom_command_service.list_commands():
        if canonicalize_saved_text_trigger(command.display_name) == lookup_key:
            return command

    return None


async def _find_smart_matches(
    raw_text: str,
    *,
    custom_command_service: CustomCommandService,
    note_service: NoteService,
    bot_runtime_settings_service: BotRuntimeSettingsService,
    smart_lookup: SmartTextLookupService,
    can_access_protected_texts: bool,
) -> tuple[SearchableTextEntry, ...]:
    candidates: list[SearchableTextEntry] = []
    if can_access_protected_texts:
        greeting_html = await bot_runtime_settings_service.get_greeting()
        if greeting_html is not None:
            candidates.append(
                SearchableTextEntry(
                    kind="greeting",
                    display_name=GREETING_TRIGGER,
                    response_html=greeting_html,
                )
            )
        candidates.extend(
            SearchableTextEntry(
                kind="note",
                display_name=note.display_name,
                response_html=note.response_html,
            )
            for note in await note_service.list_notes()
        )

    candidates.extend(
        SearchableTextEntry(
            kind="custom_command",
            display_name=command.display_name,
            response_html=command.response_html,
        )
        for command in await custom_command_service.list_commands()
    )

    matches = smart_lookup.find_matches(raw_text, tuple(candidates))
    return tuple(match.entry for match in matches)


def _build_smart_search_messages(
    matches: tuple[SearchableTextEntry, ...],
) -> tuple[str, ...]:
    blocks = [_format_smart_match_block(entry) for entry in matches]
    messages: list[str] = []
    current_message = ""
    for block in blocks:
        candidate_message = (
            block if not current_message else f"{current_message}\n\n{block}"
        )
        if len(candidate_message) <= MAX_TELEGRAM_MESSAGE_LENGTH:
            current_message = candidate_message
            continue

        if current_message:
            messages.append(current_message)
        current_message = block

    if current_message:
        messages.append(current_message)

    return tuple(messages)


def _format_smart_match_block(entry: SearchableTextEntry) -> str:
    if entry.kind == "greeting":
        title = "👋 <b>Приветствие</b>"
    elif entry.kind == "note":
        title = f"🗒 <b>Заметка:</b> <code>{escape(entry.display_name)}</code>"
    else:
        title = f"🧩 <b>Команда:</b> <code>{escape(entry.display_name)}</code>"

    return f"{title}\n\n{entry.response_html}"


def _parse_text_update_callback_data(data: str | None) -> tuple[str | None, str | None]:
    if data is None or not data.startswith(TEXT_UPDATE_PREFIX):
        return None, None

    parts = data.split(":", maxsplit=2)
    if len(parts) != 3:
        return None, None

    _, action, token = parts
    return action, token


def _format_confirmation_preview(
    *,
    entity_kind: TextEntityKind,
    display_name: str | None,
    current_html: str,
    new_html: str,
) -> str:
    entity_label = _entity_label(entity_kind)
    name_block = (
        f"🏷 Имя: <code>{escape(display_name)}</code>\n\n"
        if display_name is not None
        else ""
    )
    return (
        f"✨ <b>Такой {entity_label} уже есть.</b>\n\n"
        f"{name_block}"
        f"📄 <b>Сейчас:</b>\n{current_html}\n\n"
        f"🆕 <b>Будет сохранено:</b>\n{new_html}\n\n"
        "Выбери, что сделать с обновлением:"
    )


def _format_saved_message(
    *,
    entity_kind: TextEntityKind,
    display_name: str | None,
    was_created: bool,
    changed: bool,
) -> str:
    if was_created:
        headline = "✅ <b>Сохранено.</b>"
        details = "Новый текст успешно добавлен."
    elif changed:
        headline = "✅ <b>Сохранено.</b>"
        details = "Изменение успешно применено."
    else:
        headline = "✅ <b>Сохранено.</b>"
        details = "Текст уже был таким же, поэтому менять ничего не пришлось."

    entity_title = _entity_title(entity_kind)
    name_block = (
        f"🏷 Имя: <code>{escape(display_name)}</code>\n"
        if display_name is not None
        else ""
    )
    return f"{headline}\n\n📚 Тип: <b>{entity_title}</b>\n{name_block}📝 {details}"


def _format_confirmation_cancelled_message(
    entity_kind: TextEntityKind,
    display_name: str | None,
) -> str:
    entity_title = _entity_title(entity_kind)
    name_block = (
        f"🏷 Имя: <code>{escape(display_name)}</code>\n"
        if display_name is not None
        else ""
    )
    return (
        "🚫 <b>Изменение отменено.</b>\n\n"
        f"📚 Тип: <b>{entity_title}</b>\n"
        f"{name_block}"
        "Новый текст не был сохранён."
    )


def _format_confirmation_failure_message(
    entity_kind: TextEntityKind | None,
    display_name: str | None,
    reason: str,
) -> str:
    type_block = (
        f"📚 Тип: <b>{_entity_title(entity_kind)}</b>\n"
        if entity_kind is not None
        else ""
    )
    name_block = (
        f"🏷 Имя: <code>{escape(display_name)}</code>\n"
        if display_name is not None
        else ""
    )
    return (
        "❌ <b>Не удалось применить изменение.</b>\n\n"
        f"{type_block}"
        f"{name_block}"
        f"🛠 Причина: {escape(reason)}"
    )


def _format_save_failed_message(
    entity_label: str,
    display_name: str | None,
    reason: str,
) -> str:
    name_block = (
        f"🏷 Имя: <code>{escape(display_name)}</code>\n"
        if display_name is not None
        else ""
    )
    return f"❌ <b>Не удалось сохранить {entity_label}.</b>\n\n{name_block}🛠 {reason}"


def _entity_label(kind: TextEntityKind) -> str:
    if kind == "greeting":
        return "приветствие"
    if kind == "note":
        return "заметка"
    return "команда"


def _entity_title(kind: TextEntityKind | None) -> str:
    if kind == "greeting":
        return "Приветствие"
    if kind == "note":
        return "Заметка"
    if kind == "custom_command":
        return "Кастомная команда"
    return "Сохранённый текст"


def _normalize_text_trigger(value: str) -> str:
    return " ".join(value.split()).strip().casefold().replace("ё", "е")
