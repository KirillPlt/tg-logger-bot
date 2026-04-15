from collections.abc import Sequence
from datetime import datetime

from aiogram.types import Message

from app.application.dto import ChatUser
from app.presentation.formatters.rights import RestrictedRightsChangeSet


def build_chat_deep_link(chat_id: int) -> str:
    chat_id_as_text = str(chat_id)
    internal_chat_id = chat_id_as_text.removeprefix("-100")
    return f"tg://chat?id={internal_chat_id}"


def build_message_link(chat_id: int, message_id: int) -> str:
    chat_id_as_text = str(chat_id)
    internal_chat_id = chat_id_as_text.removeprefix("-100").lstrip("-")
    return f"https://t.me/c/{internal_chat_id}/{message_id}"


def format_message_reference(chat_id: int, message_id: int, label: str = "сообщении") -> str:
    return f"🔗 Где: <a href=\"{build_message_link(chat_id, message_id)}\">{label}</a>"


def format_user_left_message(user: ChatUser, moment: datetime) -> str:
    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"🚪 <b>Пользователь покинул группу.</b>\n"
        f"👤 Кто: {_format_user(user)}\n"
        f"🆔 ID: #id{user.id}\n\n"
        f"<b>#ПОКИНУЛ_ГРУППУ</b>"
    )


def format_user_kicked_message(user: ChatUser, admin: ChatUser, moment: datetime) -> str:
    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"🚪 <b>Администратор исключил пользователя из группы.</b>\n"
        f"🛡 Администратор: {_format_user(admin)}\n"
        f"👤 Пользователь: {_format_user(user)}\n"
        f"🆔 Админ: #id{admin.id}\n"
        f"🆔 Пользователь: #id{user.id}\n\n"
        f"<b>#АДМИН_ИСКЛЮЧИЛ_ИЗ_ГРУППЫ</b>"
    )


def format_user_added_message(
    adder: ChatUser,
    added_users: Sequence[ChatUser],
    moment: datetime,
    message_reference: str | None = None,
) -> str:
    rendered_users = "\n".join(
        f"{index}. {_format_user(user)}"
        for index, user in enumerate(added_users, start=1)
    )
    rendered_user_ids = "\n".join(f"#id{user.id}" for user in added_users)

    message_reference_block = f"{message_reference}\n\n" if message_reference else ""

    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"👥 <b>В группу добавили новых пользователей.</b>\n"
        f"🙋 Добавил: {_format_user(adder)}\n\n"
        f"{message_reference_block}"
        f"📋 Список:\n{rendered_users}\n\n"
        f"🆔 ID пользователей:\n{rendered_user_ids}\n\n"
        f"<b>#НОВЫЙ_ПОЛЬЗОВАТЕЛЬ</b>"
    )


def format_user_joined_message(user: ChatUser, moment: datetime) -> str:
    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"🎉 <b>Пользователь присоединился к группе.</b>\n"
        f"👤 Кто: {_format_user(user)}\n"
        f"🆔 ID: #id{user.id}\n\n"
        f"<b>#НОВЫЙ_ПОЛЬЗОВАТЕЛЬ</b>"
    )


def format_edited_message_notice(
    user: ChatUser,
    content_description: str,
    moment: datetime,
) -> str:
    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"✏️ <b>Пользователь изменил сообщение.</b>\n"
        f"👤 Кто: {_format_user(user)}\n"
        f"🧩 Тип содержимого: {content_description}\n"
        f"🆔 ID: #id{user.id}\n\n"
        f"<b>#ИЗМЕНИЛ_СООБЩЕНИЕ</b>"
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
        f"🔐 <b>{title}.</b>\n"
        f"👤 Пользователь: {_format_user(user)}\n"
        f"🆔 ID: #id{user.id}\n\n"
        f"📋 Что изменилось:\n{details}\n\n"
        f"<b>#ИЗМЕНИЛИ_ПРАВА</b>"
    )


def format_admin_promotion_message(
    user: ChatUser,
    rights_text: str,
    moment: datetime,
) -> str:
    return (
        f"🕒 <b>{_format_timestamp(moment)}</b>\n\n"
        f"🛡 <b>Пользователю выдали права администратора.</b>\n"
        f"👤 Пользователь: {_format_user(user)}\n"
        f"🆔 ID: #id{user.id}\n\n"
        f"📋 Выданные права:\n{rights_text}\n\n"
        f"<b>#ВЫДАЛИ_ПРАВА_АДМИНИСТРАТОРА</b>"
    )


def _format_timestamp(moment: datetime) -> str:
    return moment.strftime("%d.%m.%Y | %H:%M")


def _format_user(user: ChatUser) -> str:
    return f"{user.mention_html}{user.username_tag}"
