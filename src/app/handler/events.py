import logging

from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    ChatMemberUpdated,
    User,
    ChatJoinRequest,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import (
    ChatMemberUpdatedFilter,
    RESTRICTED,
    IS_MEMBER,
    KICKED,
    LEFT,
    ADMINISTRATOR,
    IS_NOT_MEMBER,
)

from app.bot_config.config import CHAT_ID, LOG_CHAT_ID, INFO_CHAT_ADMIN_ID
from app.database.client import ClientDB
from app.filter.user import UserOnlyAdded, UserNotAdded
from app.filter.chat import ChatId
from app.time_handler.time_now import get_time_now
from app.utils import format_rights


ChatIdFilter = ChatId(int(CHAT_ID))
LogChatIdFilter = ChatId(int(LOG_CHAT_ID))
InfoChatAdminFilter = ChatId(int(INFO_CHAT_ADMIN_ID))

rt = Router()
rt.chat_member.filter(ChatIdFilter)
rt.edited_message.filter(ChatIdFilter)
rt.message.filter(ChatIdFilter)

USER_KICKED_TRANSITION = IS_MEMBER >> (KICKED | -RESTRICTED)
USER_LEFT_TRANSITION = IS_MEMBER >> LEFT
USER_BECAME_ADMIN = (IS_MEMBER | IS_NOT_MEMBER) >> ADMINISTRATOR


ADMIN_RIGHTS = {
    "can_manage_chat": "Управление чатом",
    "can_change_info": "Изменение информации",
    "can_delete_messages": "Удаление сообщений",
    "can_restrict_members": "Мут / бан",
    "can_invite_users": "Приглашение пользователей",
    "can_pin_messages": "Закреп сообщений",
    "can_manage_topics": "Управление темами",
    "can_manage_video_chats": "Видео-чаты",
    "can_promote_members": "Назначение админов",
    "is_anonymous": "Анонимный админ",
}

RESTRICTED_RIGHTS = {
    "can_send_messages": "Отправлять сообщения",
    "can_send_photos": "Отправлять фото",
    "can_send_videos": "Отправлять видео",
    "can_send_video_notes": "Видео-кружочки",
    "can_send_voice_notes": "Голосовые",
    "can_send_audios": "Аудио",
    "can_send_documents": "Документы",
    "can_send_polls": "Опросы",
    "can_send_other_messages": "Стикеры / GIF",
    "can_invite_users": "Приглашение пользователей",
}


# Пользователь покинул чат
@rt.chat_member(ChatMemberUpdatedFilter(USER_LEFT_TRANSITION))
async def left_user_event(event: ChatMemberUpdated, log_chat_id: int) -> None:
    username: str = f"[@{event.from_user.username}]" if event.from_user.username else ""

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 <b>{get_time_now().strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
        f"🚪 Пользователь {event.from_user.mention_html()}"
        f"{username} покинул группу.\n\n"
        f"<b>#ПОКИНУЛ_ГРУППУ</b>\n"
        f"#id{event.from_user.id}",
    )


# Пользователя исключили из чата
@rt.chat_member(ChatMemberUpdatedFilter(USER_KICKED_TRANSITION))
async def admin_kick_user_event(
    event: ChatMemberUpdated, log_chat_id: int, event_from_user: User | None
) -> None:
    user_username: str = (
        f"[@{event.new_chat_member.user.username}]"
        if event.new_chat_member.user.username
        else ""
    )
    admin_username: str = (
        f"[@{event_from_user.username}]" if event_from_user.username else ""
    )

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 <b>{get_time_now().strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
        f"🚪 Пользователя {event.new_chat_member.user.mention_html()}{user_username} "
        f"<b>исключил из чата администратор</b> {event_from_user.mention_html()}{admin_username}\n\n"
        f"<b>#АДМИН_ИСКЛЮЧИЛ_ИЗ_ГРУППЫ</b>\n"
        f"Админ: #id{event_from_user.id}\n"
        f"Исключил: #id{event.new_chat_member.user.id}",
    )


@rt.message(F.new_chat_members, UserOnlyAdded())
async def user_add_user_event(message: Message, log_chat_id: int) -> None:
    if not message.new_chat_members:
        return

    users: list[str] = []
    message_lines: list[str] = []
    user_ids: list[str] = []

    for index, user in enumerate(message.new_chat_members, start=1):
        mention = user.mention_html()
        users.append(mention)
        message_lines.append(f"{index}. {mention}")
        user_ids.append(str(user.id))

    username = f" [@{message.from_user.username}]" if message.from_user.username else ""

    greeting = await ClientDB.greetings.get_greeting()
    greeting_text = greeting or ""

    await message.answer(f"👋 Привет {', '.join(users)}\n{greeting_text}")

    await message.bot.send_message(
        chat_id=log_chat_id,
        text=(
            f"🕒 <b>{get_time_now().strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
            f"🎉 Пользователь {message.from_user.mention_html()}{username} "
            f"добавил в группу:\n"
            f"{'.\n'.join(message_lines)}\n\n"
            f"<b>#НОВЫЙ_ПОЛЬЗОВАТЕЛЬ</b>\n"
            f"#id" + "\n#id".join(user_ids)
        ),
    )


# Пользователь присоединился к чату
@rt.chat_member(ChatMemberUpdatedFilter((KICKED | LEFT) >> IS_MEMBER), UserNotAdded())
async def on_user_joined(
    event: ChatMemberUpdated,
    log_chat_id: int,
    event_from_user: User | None,
) -> None:
    if event_from_user is None:
        return

    current_time = get_time_now().strftime("%d.%m.%Y | %H:%M")
    username = f" [@{event_from_user.username}]" if event_from_user.username else ""

    text = (
        f"🕒 <b>{current_time}</b>\n\n"
        f"🎉 Пользователь {event_from_user.mention_html()}{username} присоединился в группу.\n\n"
        f"<b>#НОВЫЙ_ПОЛЬЗОВАТЕЛЬ</b>\n"
        f"#id{event_from_user.id}"
    )

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=text,
    )


# Пользователь изменил сообщение
@rt.edited_message()
async def edit_message_event(event: Message, log_chat_id: int) -> None:
    if event.react:
        return

    message: str = (
        "Новое сообщение: "
        if event.text
        else "⚠️ Dev Info: Апдейт message.text вернул None. Вся информация лежит в логгах бота."
    )
    username: str = f"[@{event.from_user.username}]" if event.from_user.username else ""

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 <b>{get_time_now().strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
        f"Пользователь {event.from_user.mention_html()}{username} изменил сообщение.\n\n"
        f"<b>#ИЗМЕНИЛ_СООБЩЕНИЕ</b>\n"
        f"#id{event.from_user.id}\n"
        f"{message}",
    )

    if event.text:
        await event.bot.send_message(chat_id=log_chat_id, text=f"{event.text}")
        return

    logging.warning("Message.text вернул None", event)


# Пользователю изменили права
@rt.chat_member(ChatMemberUpdatedFilter(RESTRICTED))
async def restricted_user_event(event: ChatMemberUpdated, log_chat_id: int):
    old = event.old_chat_member
    new = event.new_chat_member

    is_admin_restricted: bool = False

    changes = []

    for attr, title in RESTRICTED_RIGHTS.items():
        try:
            old_val = getattr(old, attr)
            new_val = getattr(new, attr)

            if old_val == new_val:
                changes.append(f"{title}: {'✅' if new_val else '❌'}")
            else:
                changes.append(
                    f"{title}: {'✅' if old_val else '❌'} → {'✅' if new_val else '❌'}"
                )

        except AttributeError:
            new_val = getattr(new, attr)

            changes.append(f"{title}: {'✅' if new_val else '✅ → ❌'}")
            is_admin_restricted = True

    user = new.user
    username: str = f" [@{user.username}]" if user.username else ""
    rules_part: str = (
        "изменили права"
        if not is_admin_restricted
        else "Сняли права администратора и изменили права пользователя"
    )

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=(
            f"🕒 <b>{get_time_now().strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
            f"Пользователю {user.mention_html()}"
            f"{username}\n"
            f"<b>{rules_part}:</b>\n\n"
            f"{'\n'.join(changes)}\n"
            f"<b>#ИЗМЕНИЛИ_ПРАВА</b>\n"
            f"#id{new.user.id}"
        ),
    )


# Пользователь заходит в админский чат
@rt.chat_join_request(InfoChatAdminFilter)
async def user_join_in_admin_chat(request: ChatJoinRequest, bot: Bot):
    admins = await bot.get_chat_administrators(int(CHAT_ID))
    for admin in admins:
        if request.from_user.id == admin.user.id:
            await request.approve()
            return
    await request.decline()


# Пользователь заходит в лог-чат
@rt.chat_join_request(LogChatIdFilter)
async def user_join_in_log_chat(request: ChatJoinRequest, bot: Bot):
    admins = await bot.get_chat_administrators(int(CHAT_ID))
    for admin in admins:
        if request.from_user.id == admin.user.id:
            await request.approve()
            return
    await request.decline()


# Пользователю изменили права или права администратора
@rt.chat_member()
async def admin_promoted(event: ChatMemberUpdated, log_chat_id: int):
    new = event.new_chat_member

    if new.status != "administrator":
        return

    admin_rights_text = format_rights(new, ADMIN_RIGHTS)
    user = new.user
    username: str = f" [@{user.username}]" if user.username else ""

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=(
            f"🕒 <b>{get_time_now().strftime('%d.%m.%Y | %H:%M')}</b>\n\n"
            f"Пользователю {user.mention_html()}"
            f"{username}\n"
            f"выдали <b>права администратора</b>:\n\n"
            f"{admin_rights_text}\n\n"
            f"<b>#ВЫДАЛИ_ПРАВА_АДМИНИСТРАТОРА</b>\n"
            f"#id{user.id}"
        ),
    )

    await event.bot.send_message(
        chat_id=CHAT_ID,
        text=f"✉️ {user.mention_html()}, так как тебя назначили администратором, "
        f"просим тебя вступить в наши чаты "
        f"доступным только нашей администрации: ",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⚙️ Лог чат", url="https://t.me/+gPmxiepnJWFhMjAy"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛡 Инфо-админ", url="https://t.me/+eDiObhj7a6wyZGU6"
                    )
                ],
            ]
        ),
    )
