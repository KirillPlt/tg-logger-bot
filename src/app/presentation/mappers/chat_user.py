from collections.abc import Iterable

from aiogram.types import User

from app.application.dto import ChatUser


def map_chat_user(user: User) -> ChatUser:
    return ChatUser(
        id=user.id,
        mention_html=user.mention_html(),
        username=user.username,
    )


def map_chat_users(users: Iterable[User]) -> tuple[ChatUser, ...]:
    return tuple(map_chat_user(user) for user in users)
