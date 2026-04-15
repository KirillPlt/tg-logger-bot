from dataclasses import replace

from app.application.protocols import ChatStateRepository
from app.domain.models import ChatState


class ChatStateService:
    def __init__(self, repository: ChatStateRepository) -> None:
        self._repository = repository

    async def get_or_create(self, chat_id: int) -> ChatState:
        state = await self._repository.get(chat_id)
        return state if state is not None else ChatState(chat_id=chat_id)

    async def update_title(self, chat_id: int, title: str) -> tuple[str | None, ChatState]:
        state = await self.get_or_create(chat_id)
        updated_state = replace(state, title=title)
        await self._repository.upsert(updated_state)
        return state.title, updated_state

    async def update_photo(
        self,
        chat_id: int,
        file_unique_id: str | None,
    ) -> tuple[str | None, ChatState]:
        state = await self.get_or_create(chat_id)
        updated_state = replace(state, photo_file_unique_id=file_unique_id)
        await self._repository.upsert(updated_state)
        return state.photo_file_unique_id, updated_state

    async def update_auto_delete_timer(
        self,
        chat_id: int,
        auto_delete_time_seconds: int | None,
    ) -> tuple[int | None, ChatState]:
        state = await self.get_or_create(chat_id)
        updated_state = replace(
            state,
            auto_delete_time_seconds=auto_delete_time_seconds,
        )
        await self._repository.upsert(updated_state)
        return state.auto_delete_time_seconds, updated_state

