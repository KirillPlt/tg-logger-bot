from typing import Protocol

from app.domain.models import ChatState


class ChatStateRepository(Protocol):
    async def get(self, chat_id: int) -> ChatState | None:
        ...

    async def upsert(self, state: ChatState) -> None:
        ...

