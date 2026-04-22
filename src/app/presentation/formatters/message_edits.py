from datetime import datetime

from app.application.dto import ChatUser
from app.domain.models import MessageSnapshot


def format_edited_message_diff(
    *,
    user: ChatUser,
    content_description: str,
    previous_snapshot: MessageSnapshot | None,
    current_payload: str | None,
    moment: datetime,
    message_reference: str | None = None,
) -> str | None:
    previous_payload = (
        previous_snapshot.rendered_html if previous_snapshot is not None else None
    )
    old_value = (
        previous_payload
        or "<i>Неизвестно: предыдущая версия сообщения не была сохранена.</i>"
    )
    new_value = current_payload or "<i>Новое содержимое недоступно.</i>"
    message_reference_block = f"{message_reference}\n" if message_reference else ""

    if previous_payload != current_payload:
        return (
            f"🕒 <b>{moment.strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
            f"✏️ <b>Пользователь изменил сообщение.</b>\n"
            f"👤 Кто: {user.mention_html}{user.username_tag}\n"
            f"{message_reference_block}"
            f"🧩 Тип содержимого: {content_description}\n"
            f"🆔 ID: #id{user.id}\n\n"
            f"⬅️ <b>Было:</b>\n{old_value}\n\n"
            f"➡️ <b>Стало:</b>\n{new_value}\n\n"
            f"<b>#ИЗМЕНИЛ_СООБЩЕНИЕ</b>"
        )
    return None
