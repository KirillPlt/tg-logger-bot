from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated, User
from aiogram.filters import ChatMemberUpdatedFilter, RESTRICTED, IS_MEMBER, KICKED, LEFT

from app.bot_config.config import CHAT_ID, LOG_CHAT_ID
from app.filter.user import UserOnlyAdded, UserNotAdded
from app.filter.chat import ChatId
from app.time_handler.time_now import get_time_now
from app.utils import user_rules_analysis

ChatIdFilter = ChatId(int(CHAT_ID))
LogChatIdFilter = ChatId(int(LOG_CHAT_ID))

rt = Router()
rt.chat_member.filter(LogChatIdFilter)
rt.edited_message.filter(LogChatIdFilter)
rt.message.filter(LogChatIdFilter)

USER_KICKED_TRANSITION = (IS_MEMBER >> (KICKED | -RESTRICTED))
USER_LEFT_TRANSITION = (IS_MEMBER >> LEFT)


# Пользователь покинул чат
@rt.chat_member(ChatMemberUpdatedFilter(USER_LEFT_TRANSITION))
async def left_user_event(
    event: ChatMemberUpdated,
    log_chat_id: int,
) -> None:

    print(event.from_user.id)

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 Дата и время: {get_time_now().strftime("%d.%m.%Y | %H:%M")}\n"
             f"🚪 Пользователь {event.from_user.mention_html()}"
             f"{f"[@{event.from_user.username}]" if event.from_user.username else ""} покинул группу.\n"
             f"#ПОКИНУЛ_ГРУППУ_{event.from_user.id}",
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
        text=f"🕒 Дата и время: {get_time_now().strftime("%d.%m.%Y | %H:%M")}\n"
             f"🚪 Пользователя {event.new_chat_member.user.mention_html()}"
             f"{f"[@{event.new_chat_member.user.username}]" if event.new_chat_member.user.username else ""} "
             f"исключил из чата администратор {event_from_user.mention_html()}"
             f"{f"[@{event_from_user.username}]" if event_from_user.username else ""}\n"
             f"#АДМИН_{event_from_user.id}_ИСКЛЮЧИЛ_ИЗ_ГРУППЫ_{event.new_chat_member.user.id}",
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
        text=f"🕒 Дата и время: {get_time_now().strftime("%d.%m.%Y | %H:%M")}\n"
             f"🎉 Пользователь {message.from_user.mention_html()}"
             f"{f"[@{message.from_user.username}]" if message.from_user.username else ""} добавил в группу:\n"
             f"{message_answer}\n"
             f"#НОВЫЙ_ПОЛЬЗОВАТЕЛЬ_{user_ids}",
    )


# Пользователь присоединился к чату
@rt.chat_member(ChatMemberUpdatedFilter((KICKED | LEFT) >> IS_MEMBER), UserNotAdded())
async def join_user_event(event: ChatMemberUpdated, log_chat_id: int, event_from_user: User | None) -> None:
    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 Дата и время: {get_time_now().strftime("%d.%m.%Y | %H:%M")}\n"
             f"🎉 Пользователь {event_from_user.mention_html()}{f"[@{event_from_user.username}]" if event_from_user.username else ""} присоеденился в группу.\n"
             f"#НОВЫЙ_ПОЛЬЗОВАТЕЛЬ_{event_from_user.id}",
    )


# Пользователь изменил сообщение
@rt.edited_message()
async def edit_message_event(event: Message, log_chat_id: int) -> None:
    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 Дата и время: {get_time_now().strftime("%d.%m.%Y | %H:%M")}\n"
             f"Пользователь {event.from_user.mention_html()}{f"[@{event.from_user.username}]" if event.from_user.username else ""} изменил сообщение.\n"
             f"#ИЗМЕНИЛ_СООБЩЕНИЕ_{event.from_user.id}\n"
             f"Новое сообщение:"
    )
    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"{event.text}"
    )


# Пользователю изменили права
@rt.chat_member(ChatMemberUpdatedFilter(RESTRICTED))
async def restricted_user_event(event: ChatMemberUpdated, log_chat_id: int) -> None:
    old_rules: list[bool] = [
        event.old_chat_member.can_send_audios,  # Может отправлять аудио
        event.old_chat_member.can_send_documents,  # Может отправлять документы
        event.old_chat_member.can_send_messages,  # Может отправлять сообщения
        event.old_chat_member.can_send_other_messages,  # Может отправлять стикеры, GIF и т.д.
        event.old_chat_member.can_send_photos,  # Может отправлять фото
        event.old_chat_member.can_send_polls,  # Может отправлять опросы
        event.old_chat_member.can_send_video_notes,  # Может отправлять видео-кружочки
        event.old_chat_member.can_send_videos,  # Может отправлять видео
        event.old_chat_member.can_send_voice_notes,  # Может отправлять ГС
    ]

    new_rules: list[bool] = [
        event.new_chat_member.can_send_audios,  # Может отправлять аудио
        event.new_chat_member.can_send_documents,  # Может отправлять документы
        event.new_chat_member.can_send_messages,  # Может отправлять сообщения
        event.new_chat_member.can_send_other_messages,  # Может отправлять стикеры, GIF и т.д.
        event.new_chat_member.can_send_photos,  # Может отправлять фото
        event.new_chat_member.can_send_polls,  # Может отправлять опросы
        event.new_chat_member.can_send_video_notes,  # Может отправлять видео-кружочки
        event.new_chat_member.can_send_videos,  # Может отправлять видео
        event.new_chat_member.can_send_voice_notes,  # Может отправлять ГС
    ]

    rules = user_rules_analysis(old_rules, new_rules)

    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 Дата и время: {get_time_now().strftime("%d.%m.%Y | %H:%M")}\n"
             f"Пользователю {event.new_chat_member.user.mention_html()}"
             f"{f"[@{event.new_chat_member.user.username}]" if event.new_chat_member.user.username else ""} изменили права.\n"
             f"Теперь он:\n"
             f"{rules}"
    )
