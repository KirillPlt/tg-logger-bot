import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated, User, ChatJoinRequest, ChatMemberAdministrator, ChatMember
from aiogram.filters import ChatMemberUpdatedFilter, RESTRICTED, IS_MEMBER, KICKED, LEFT, ADMINISTRATOR, IS_NOT_MEMBER

from app.bot_config.config import CHAT_ID, LOG_CHAT_ID
from app.filter.user import UserOnlyAdded, UserNotAdded, IsAdmin
from app.filter.chat import ChatId
from app.time_handler.time_now import get_time_now
from app.utils import format_rights

ChatIdFilter = ChatId(int(CHAT_ID))
LogChatIdFilter = ChatId(int(LOG_CHAT_ID))

rt = Router()
rt.chat_member.filter(ChatIdFilter)
rt.edited_message.filter(ChatIdFilter)
rt.message.filter(ChatIdFilter)

USER_KICKED_TRANSITION = (IS_MEMBER >> (KICKED | -RESTRICTED))
USER_LEFT_TRANSITION = (IS_MEMBER >> LEFT)
USER_BECAME_ADMIN = ((IS_MEMBER | IS_NOT_MEMBER) >> ADMINISTRATOR)


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
    "can_invite_users": "Приглашать пользователей",
    "can_pin_messages": "Закреплять сообщения",
    "can_change_info": "Менять информацию",
}


# Пользователь покинул чат
@rt.chat_member(ChatMemberUpdatedFilter(USER_LEFT_TRANSITION))
async def left_user_event(
    event: ChatMemberUpdated,
    log_chat_id: int,
) -> None:

    print(event.from_user.id)

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 <b>{get_time_now().strftime("%d.%m.%Y | %H:%M")}</b>\n"
             f"🚪 Пользователь {event.from_user.mention_html()}"
             f"{f"[@{event.from_user.username}]" if event.from_user.username else ""} покинул группу.\n"
             f"<b>#ПОКИНУЛ_ГРУППУ_{event.from_user.id}</b>",
    )


# Пользователя исключили из чата
@rt.chat_member(ChatMemberUpdatedFilter(USER_KICKED_TRANSITION))
async def admin_kick_user_event(
    event: ChatMemberUpdated,
    log_chat_id: int,
    event_from_user: User | None
) -> None:

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 <b>{get_time_now().strftime("%d.%m.%Y | %H:%M")}</b>\n"
             f"🚪 Пользователя {event.new_chat_member.user.mention_html()}"
             f"{f"[@{event.new_chat_member.user.username}]" if event.new_chat_member.user.username else ""} "
             f"<b>исключил из чата администратор</b> {event_from_user.mention_html()}"
             f"{f"[@{event_from_user.username}]" if event_from_user.username else ""}\n"
             f"<b>#АДМИН_{event_from_user.id}_ИСКЛЮЧИЛ_ИЗ_ГРУППЫ_{event.new_chat_member.user.id}</b>",
    )


# Пользователя добавил другой пользователь
@rt.message(F.new_chat_members, UserOnlyAdded())
async def user_add_user_event(message: Message, log_chat_id: int) -> None:
    message_answer: str = ""
    user_ids: str = ""
    user_count: int = 1

    for user in message.new_chat_members[0:-1]:
        message_answer += f"{user_count}. {user.mention_html()},\n"
        user_ids += (str(user.id) + "_")
        user_count += 1
    else:
        message_answer += f"{user_count}. {message.new_chat_members[-1].mention_html()}."
        user_ids += (str(message.new_chat_members[-1].id))

    await message.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 <b>{get_time_now().strftime("%d.%m.%Y | %H:%M")}</b>\n"
             f"🎉 Пользователь {message.from_user.mention_html()}"
             f"{f"[@{message.from_user.username}]" if message.from_user.username else ""} добавил в группу:\n"
             f"{message_answer}\n"
             f"<b>#НОВЫЙ_ПОЛЬЗОВАТЕЛЬ_{user_ids}</b>",
    )


# Пользователь присоединился к чату
@rt.chat_member(ChatMemberUpdatedFilter((KICKED | LEFT) >> IS_MEMBER), UserNotAdded())
async def join_user_event(event: ChatMemberUpdated, log_chat_id: int, event_from_user: User | None) -> None:
    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 <b>{get_time_now().strftime("%d.%m.%Y | %H:%M")}</b>\n"
             f"🎉 Пользователь {event_from_user.mention_html()}{f"[@{event_from_user.username}]" if event_from_user.username else ""} присоеденился в группу.\n"
             f"<b>#НОВЫЙ_ПОЛЬЗОВАТЕЛЬ_{event_from_user.id}<b/>",
    )


# Пользователь изменил сообщение
@rt.edited_message()
async def edit_message_event(event: Message, log_chat_id: int) -> None:
    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 <b>{ get_time_now().strftime("%d.%m.%Y | %H:%M") }</b>\n"
             f"Пользователь { event.from_user.mention_html() }{ f"[@{ event.from_user.username }]" if event.from_user.username else "" } изменил сообщение.\n"
             f"<b>#ИЗМЕНИЛ_СООБЩЕНИЕ_{ event.from_user.id }</b>\n"
             f"{ "Новое сообщение: " if event.text else "⚠️ Dev Info: Апдейт message.text вернул None. Вся информация лежит в логгах бота." }"
    )

    if event.text:
        await event.bot.send_message(
            chat_id=log_chat_id,
            text=f"{event.text}"
        )
        return

    logging.warning("Message.text вернул None", event)


# Пользователю изменили права
@rt.chat_member(ChatMemberUpdatedFilter(RESTRICTED))
async def restricted_user_event(event: ChatMemberUpdated, log_chat_id: int):
    old = event.old_chat_member
    new = event.new_chat_member
    rights_text: str = ""

    changes = []

    for attr, title in RESTRICTED_RIGHTS.items():
        try:
            old_val = getattr(old, attr)
            new_val = getattr(new, attr)

            if old_val == new_val:
                changes.append(
                    f"{title}: {'✅' if new_val else '❌'}\n"
                )
            else:
                changes.append(
                    f"{title}: {'✅' if old_val else '❌'} → {'✅' if new_val else '❌'}\n"
                )

        except AttributeError:
            rights_text = format_rights(new, ADMIN_RIGHTS)
    user = new.user

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=(
            f"🕒 <b>{get_time_now().strftime('%d.%m.%Y | %H:%M')}</b>\n"
            f"Пользователю {user.mention_html()}"
            f"{f' [@{user.username}]' if user.username else ''}\n"
            f"<b>изменили права:</b>\n\n {'\n'.join(changes) if changes else rights_text}"
            f"<b>#ИЗМЕНИЛИ_ПРАВА_{new.user.id}</b>"
        )
    )


# Пользователь заходит в лог-чат
@rt.chat_join_request(LogChatIdFilter)
async def user_join_in_log_chat(request: ChatJoinRequest, bot: Bot):
    admins = await bot.get_chat_administrators(int(CHAT_ID))
    for admin in admins:
        if request.from_user.id == admin.user.id:
            await request.approve()
            return
    await request.decline()


# Пользователю изменили права администратора
@rt.chat_member()
async def admin_promoted(event: ChatMemberUpdated, log_chat_id: int):
    new = event.new_chat_member

    if new.status != "administrator":
        return

    rights_text = format_rights(new, ADMIN_RIGHTS)
    user = new.user

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=(
            f"🕒 <b>{get_time_now().strftime('%d.%m.%Y | %H:%M')}</b>\n"
            f"Пользователю {user.mention_html()}"
            f"{f' [@{user.username}]' if user.username else ''}\n"
            f"выдали <b>права администратора</b>:\n\n"
            f"{rights_text}"
            f"<b>#ВЫДАЛИ_ПРАВА_АДМИНИСТРАТОРА_{user.id}</b>"
        )
    )