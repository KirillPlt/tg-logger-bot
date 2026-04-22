from app.application.services import ChatStateService
from app.domain.models import ChatState


class InMemoryChatStateRepository:
    def __init__(self) -> None:
        self._states: dict[int, ChatState] = {}

    async def get(self, chat_id: int) -> ChatState | None:
        return self._states.get(chat_id)

    async def upsert(self, state: ChatState) -> None:
        self._states[state.chat_id] = state


async def test_chat_state_service_tracks_previous_title() -> None:
    service = ChatStateService(InMemoryChatStateRepository())

    previous_title, updated_state = await service.update_title(-100123, "Новое имя")

    assert previous_title is None
    assert updated_state.title == "Новое имя"

    previous_title, updated_state = await service.update_title(-100123, "Еще новее")

    assert previous_title == "Новое имя"
    assert updated_state.title == "Еще новее"
