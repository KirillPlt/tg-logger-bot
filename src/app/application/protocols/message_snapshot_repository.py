from typing import Protocol

from app.domain.models import MessageSnapshot


class MessageSnapshotRepository(Protocol):
    async def get(self, chat_id: int, message_id: int) -> MessageSnapshot | None: ...

    async def upsert(self, snapshot: MessageSnapshot) -> None: ...
