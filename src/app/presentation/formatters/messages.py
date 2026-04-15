from collections.abc import Sequence
from datetime import datetime

from aiogram.types import Message

from app.application.dto import ChatUser
from app.presentation.formatters.rights import RestrictedRightsChangeSet


def build_chat_deep_link(chat_id: int) -> str:
    chat_id_as_text = str(chat_id)
    internal_chat_id = chat_id_as_text.removeprefix("-100")
    return f"tg://chat?id={internal_chat_id}"


def format_user_left_message(user: ChatUser, moment: datetime) -> str:
    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"🚪 Пользователь {_format_user(user)} покинул группу.\n\n"
        f"<b>#ПОКИНУЛ_ГРУППУ</b>\n"
        f"#id{user.id}"
    )


def format_user_kicked_message(user: ChatUser, admin: ChatUser, moment: datetime) -> str:
    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"🚪 Пользователя {_format_user(user)} "
        f"<b>исключил из чата администратор</b> {_format_user(admin)}\n\n"
        f"<b>#АДМИН_ИСКЛЮЧИЛ_ИЗ_ГРУППЫ</b>\n"
        f"Админ: #id{admin.id}\n"
        f"Исключил: #id{user.id}"
    )


def format_user_added_message(
    adder: ChatUser,
    added_users: Sequence[ChatUser],
    moment: datetime,
) -> str:
    rendered_users = "\n".join(
        f"{index}. {_format_user(user)}"
        for index, user in enumerate(added_users, start=1)
    )
    rendered_user_ids = "\n".join(f"#id{user.id}" for user in added_users)

    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"🎉 Пользователь {_format_user(adder)} добавил в группу:\n"
        f"{rendered_users}\n\n"
        f"<b>#НОВЫЙ_ПОЛЬЗОВАТЕЛЬ</b>\n"
        f"{rendered_user_ids}"
    )


def format_user_joined_message(user: ChatUser, moment: datetime) -> str:
    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"🎉 Пользователь {_format_user(user)} присоединился в группу.\n\n"
        f"<b>#НОВЫЙ_ПОЛЬЗОВАТЕЛЬ</b>\n"
        f"#id{user.id}"
    )


def format_edited_message_notice(
    user: ChatUser,
    content_description: str,
    moment: datetime,
) -> str:
    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"✏️ Пользователь {_format_user(user)} изменил сообщение.\n"
        f"Тип содержимого: {content_description}\n\n"
        f"<b>#ИЗМЕНИЛ_СООБЩЕНИЕ</b>\n"
        f"#id{user.id}"
    )


def extract_edited_message_payload(message: Message) -> str | None:
    return message.html_text


def describe_edited_message_content(message: Message) -> str:
    if message.text:
        return "текст"

    if message.caption:
        return "подпись к медиа"

    return str(message.content_type)


def format_user_restricted_message(
    user: ChatUser,
    change_set: RestrictedRightsChangeSet,
    moment: datetime,
) -> str:
    title = (
        "Сняли права администратора и изменили права пользователя"
        if change_set.includes_admin_demotion
        else "Изменили права пользователя"
    )
    details = "\n".join(change_set.lines) if change_set.lines else "Права администратора сняты."

    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"Пользователю {_format_user(user)}\n"
        f"<b>{title}:</b>\n\n"
        f"{details}\n\n"
        f"<b>#ИЗМЕНИЛИ_ПРАВА</b>\n"
        f"#id{user.id}"
    )


def format_admin_promotion_message(
    user: ChatUser,
    rights_text: str,
    moment: datetime,
) -> str:
    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"Пользователю {_format_user(user)}\n"
        f"выдали <b>права администратора</b>:\n\n"
        f"{rights_text}\n\n"
        f"<b>#ВЫДАЛИ_ПРАВА_АДМИНИСТРАТОРА</b>\n"
        f"#id{user.id}"
    )


def _format_timestamp(moment: datetime) -> str:
    return moment.strftime("%d.%m.%Y | %H:%M")


def _format_user(user: ChatUser) -> str:
    return f"{user.mention_html}{user.username_tag}"
