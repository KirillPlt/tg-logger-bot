from __future__ import annotations

from datetime import datetime

from aiogram.types import InaccessibleMessage, Message

from app.application.services import ChatStateService
from app.presentation.formatters.messages import format_message_reference


async def describe_service_message(
    *,
    message: Message,
    chat_state_service: ChatStateService,
) -> str | None:
    if message.from_user is None:
        actor = "🤖 Система"
    else:
        username_tag = f" [@{message.from_user.username}]" if message.from_user.username else ""
        actor = f"{message.from_user.mention_html()}{username_tag}"

    timestamp = message.date.strftime("%d.%m.%Y | %H:%M")
    chat_id = message.chat.id
    service_message_reference = format_message_reference(chat_id, message.message_id)

    if message.new_chat_title is not None:
        previous_title, _ = await chat_state_service.update_title(chat_id, message.new_chat_title)
        return _render(
            timestamp,
            f"📝 {actor} изменил название чата.\n"
            f"⬅️ Было: <b>{previous_title or 'Неизвестно'}</b>\n"
            f"➡️ Стало: <b>{message.new_chat_title}</b>",
            "ИЗМЕНИЛИ_НАЗВАНИЕ_ЧАТА",
            message_reference=service_message_reference,
        )

    if message.new_chat_photo:
        previous_photo_id, _ = await chat_state_service.update_photo(
            chat_id,
            message.new_chat_photo[-1].file_unique_id,
        )
        previous_state = "была" if previous_photo_id is not None else "не была установлена"
        return _render(
            timestamp,
            f"🖼 {actor} обновил фотографию чата.\n"
            f"⬅️ Предыдущая фотография: <b>{previous_state}</b>\n"
            f"➡️ Новая фотография: <b>установлена</b>",
            "ИЗМЕНИЛИ_ФОТО_ЧАТА",
            message_reference=service_message_reference,
        )

    if message.delete_chat_photo:
        previous_photo_id, _ = await chat_state_service.update_photo(chat_id, None)
        return _render(
            timestamp,
            f"🗑 {actor} удалил фотографию чата.\n"
            f"🖼 Фотография была установлена: <b>{'Да' if previous_photo_id is not None else 'Неизвестно'}</b>",
            "УДАЛИЛИ_ФОТО_ЧАТА",
            message_reference=service_message_reference,
        )

    if message.message_auto_delete_timer_changed is not None:
        new_seconds = message.message_auto_delete_timer_changed.message_auto_delete_time
        previous_seconds, _ = await chat_state_service.update_auto_delete_timer(chat_id, new_seconds)
        return _render(
            timestamp,
            f"⏳ {actor} изменил таймер автоудаления сообщений.\n"
            f"⬅️ Было: <b>{_format_auto_delete_timer(previous_seconds)}</b>\n"
            f"➡️ Стало: <b>{_format_auto_delete_timer(new_seconds)}</b>",
            "ИЗМЕНИЛИ_ТАЙМЕР_АВТОУДАЛЕНИЯ",
            message_reference=service_message_reference,
        )

    if message.pinned_message is not None:
        pinned_message = message.pinned_message
        pinned_message_reference = format_message_reference(chat_id, pinned_message.message_id)
        pinned_preview = (
            pinned_message.html_text
            if isinstance(pinned_message, Message)
            else "<i>Недоступно: Telegram не прислал содержимое закрепленного сообщения.</i>"
        )
        return _render(
            timestamp,
            f"📌 {actor} закрепил сообщение.\n\n"
            f"{pinned_message_reference}\n\n"
            f"💬 <b>Закрепленное сообщение:</b>\n{pinned_preview}",
            "ЗАКРЕПИЛИ_СООБЩЕНИЕ",
        )

    if message.video_chat_scheduled is not None:
        start_date = message.video_chat_scheduled.start_date.strftime("%d.%m.%Y | %H:%M")
        return _render(
            timestamp,
            f"🎥 {actor} запланировал видеочат на <b>{start_date}</b>.",
            "ЗАПЛАНИРОВАЛИ_ВИДЕОЧАТ",
            message_reference=service_message_reference,
        )

    if message.video_chat_started is not None:
        return _render(
            timestamp,
            f"🎥 {actor} начал видеочат.",
            "НАЧАЛИ_ВИДЕОЧАТ",
            message_reference=service_message_reference,
        )

    if message.video_chat_ended is not None:
        duration = message.video_chat_ended.duration
        return _render(
            timestamp,
            f"🎥 {actor} завершил видеочат.\n"
            f"⏱ Длительность: <b>{duration} сек.</b>",
            "ЗАВЕРШИЛИ_ВИДЕОЧАТ",
            message_reference=service_message_reference,
        )

    if message.video_chat_participants_invited is not None:
        invited_users = ", ".join(user.mention_html() for user in message.video_chat_participants_invited.users)
        return _render(
            timestamp,
            f"🎥 {actor} пригласил участников в видеочат:\n{invited_users}",
            "ПРИГЛАСИЛИ_В_ВИДЕОЧАТ",
            message_reference=service_message_reference,
        )

    if message.forum_topic_created is not None:
        return _render(
            timestamp,
            f"🧵 {actor} создал тему форума <b>{message.forum_topic_created.name}</b>.",
            "СОЗДАЛИ_ТЕМУ",
            message_reference=service_message_reference,
        )

    if message.forum_topic_edited is not None:
        edited_name = message.forum_topic_edited.name or "Без изменения названия"
        return _render(
            timestamp,
            f"🧵 {actor} изменил тему форума.\n"
            f"📝 Новое название: <b>{edited_name}</b>",
            "ИЗМЕНИЛИ_ТЕМУ",
            message_reference=service_message_reference,
        )

    if message.forum_topic_closed is not None:
        return _render(
            timestamp,
            f"🧵 {actor} закрыл тему форума.",
            "ЗАКРЫЛИ_ТЕМУ",
            message_reference=service_message_reference,
        )

    if message.forum_topic_reopened is not None:
        return _render(
            timestamp,
            f"🧵 {actor} снова открыл тему форума.",
            "ОТКРЫЛИ_ТЕМУ",
            message_reference=service_message_reference,
        )

    if message.general_forum_topic_hidden is not None:
        return _render(
            timestamp,
            f"🧵 {actor} скрыл общую тему форума.",
            "СКРЫЛИ_ОБЩУЮ_ТЕМУ",
            message_reference=service_message_reference,
        )

    if message.general_forum_topic_unhidden is not None:
        return _render(
            timestamp,
            f"🧵 {actor} открыл общую тему форума.",
            "ОТКРЫЛИ_ОБЩУЮ_ТЕМУ",
            message_reference=service_message_reference,
        )

    if message.group_chat_created or message.supergroup_chat_created or message.channel_chat_created:
        return _render(
            timestamp,
            "ℹ️ Telegram создал системное сообщение о создании чата.",
            "СОЗДАН_ЧАТ",
            message_reference=service_message_reference,
        )

    if message.migrate_to_chat_id is not None:
        return _render(
            timestamp,
            f"➡️ Чат мигрировал в supergroup.\n"
            f"🆔 Новый chat_id: <code>{message.migrate_to_chat_id}</code>",
            "МИГРАЦИЯ_ЧАТА",
            message_reference=service_message_reference,
        )

    if message.migrate_from_chat_id is not None:
        return _render(
            timestamp,
            f"⬅️ Текущий чат был создан миграцией из chat_id <code>{message.migrate_from_chat_id}</code>.",
            "МИГРАЦИЯ_ЧАТА",
            message_reference=service_message_reference,
        )

    if message.boost_added is not None:
        return _render(
            timestamp,
            f"🚀 {actor} добавил буст чату.\n"
            f"📈 Количество бустов: <b>{message.boost_added.boost_count}</b>",
            "ДОБАВИЛИ_БУСТ",
            message_reference=service_message_reference,
        )

    return None


def get_renderable_message_html(message: Message) -> str | None:
    return message.html_text


def _render(
    timestamp: str,
    body: str,
    hashtag: str,
    message_reference: str | None = None,
) -> str:
    message_reference_block = f"{message_reference}\n\n" if message_reference else ""

    return (
        f"🕒 <b>{timestamp}</b>\n\n"
        f"{body}\n\n"
        f"{message_reference_block}"
        f"<b>#{hashtag}</b>"
    )


def _format_auto_delete_timer(seconds: int | None) -> str:
    if seconds is None or seconds == 0:
        return "🔕 Выключен"
    return f"{seconds} сек."
