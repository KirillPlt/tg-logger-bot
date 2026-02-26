from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated, User
from aiogram.filters import ChatMemberUpdatedFilter, RESTRICTED, IS_MEMBER, KICKED, LEFT

from app.time_handler.time_now import get_time_now

rt = Router()

USER_KICKED_TRANSITION = (IS_MEMBER >> (KICKED | -RESTRICTED))
USER_LEFT_TRANSITION = (IS_MEMBER >> LEFT)


# Пользователь покинул чат
@rt.chat_member(ChatMemberUpdatedFilter(USER_LEFT_TRANSITION))
async def left_user_event(event: ChatMemberUpdated, log_chat_id: int, event_from_user: User | None) -> None:
    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 Дата и время: {get_time_now().strftime("%d.%m.%Y | %h:%M")}]\n"
             f"🚪 Пользователь {event_from_user.full_name}[{event_from_user.id}] покинул группу.\n"
             f"#ПОКИНУЛ_ГРУППУ_{event_from_user.id}",
    )


# Пользователя исключили из чата
@rt.chat_member(ChatMemberUpdatedFilter(USER_KICKED_TRANSITION))
async def admin_kick_user_event(event: ChatMemberUpdated, log_chat_id: int, event_from_user: User | None) -> None:
    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 Дата и время: {get_time_now().strftime("%d.%m.%Y | %h:%M")}\n"
             f"🚪 Пользователя {event.new_chat_member.user.full_name}[{event.new_chat_member.user.id}] исключил из чата"
             f" администратор {event_from_user.full_name}[{event_from_user.id}]\n"
             f"#ИСКЛЮЧИЛИ_ИЗ_ГРУППЫ_{event_from_user.id}",
    )

# Пользователь присоединился к чату
@rt.chat_member(ChatMemberUpdatedFilter((KICKED | -RESTRICTED) >> IS_MEMBER))
async def join_user_event(event: ChatMemberUpdated, log_chat_id: int, event_from_user: User | None) -> None:
    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 Дата и время: {get_time_now().strftime("%d.%m.%Y | %h:%M")}\n"
             f"🎉 Пользователь {event_from_user.full_name}[{event_from_user.id}] присоеденился группу.\n"
             f"#НОВЫЙ_ПОЛЬЗОВАТЕЛЬ_{event_from_user.id}",
    )

# Пользователь изменил сообщение
@rt.edited_message()
async def edit_message_event(event: Message, log_chat_id: int) -> None:
    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 Дата и время: {get_time_now().strftime("%d.%m.%Y | %h:%M")}\n"
             f"Пользователь {event.from_user.full_name}[{event.from_user.id}] изменил сообщение.\n"
             f"#ИЗМЕНИЛ_СООБЩЕНИЕ_{event.from_user.id}\n"
             f"Новое сообщение:"
    )
    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"{event.text}"
    )

@rt.chat_member(ChatMemberUpdatedFilter(RESTRICTED))
async def restricted_user_event(event: ChatMemberUpdated, log_chat_id: int) -> None:
    await event.bot.send_message(
        chat_id=log_chat_id,
        text=f"🕒 Дата и время: {get_time_now().strftime("%d.%m.%Y | %h:%M")}\n"
             f"Пользователю {event.new_chat_member.user.full_name}[{event.new_chat_member.user.id}] изменили права."
    )
