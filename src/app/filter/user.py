from aiogram.filters import BaseFilter
from aiogram.types import Message, ChatMemberUpdated


# Фильтр создан исключительно для F.new_chat_members, т.к. он пиздит апдейт у ChatMemberUpdatedFilter.
class UserOnlyAdded(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        return msg.from_user.id != msg.new_chat_members[0].id


class UserNotAdded(BaseFilter):
    async def __call__(self, event: ChatMemberUpdated | Message) -> bool:
        if isinstance(event, Message):
            return event.from_user.id == event.new_chat_members[0].id
        return event.from_user.id == event.new_chat_member.user.id
