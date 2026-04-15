from app.application.protocols import MessageSnapshotRepository
from app.domain.models import MessageSnapshot


class MessageSnapshotService:
    def __init__(self, repository: MessageSnapshotRepository) -> None:
        self._repository = repository

    async def get(self, chat_id: int, message_id: int) -> MessageSnapshot | None:
        return await self._repository.get(chat_id, message_id)

    async def save(
        self,
        chat_id: int,
        message_id: int,
        content_type: str,
        rendered_html: str | None,
    ) -> MessageSnapshot:
        snapshot = MessageSnapshot(
            chat_id=chat_id,
            message_id=message_id,
            content_type=content_type,
            rendered_html=rendered_html.strip() if rendered_html else None,
        )
        await self._repository.upsert(snapshot)
        return snapshot
