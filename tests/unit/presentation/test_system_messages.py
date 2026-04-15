from datetime import datetime, timezone

from aiogram.types import Chat, Message, MessageAutoDeleteTimerChanged, User

from app.application.services import ChatStateService
from app.domain.models import ChatState
from app.presentation.formatters import describe_service_message


class InMemoryChatStateRepository:
    def __init__(self) -> None:
        self._states: dict[int, ChatState] = {}

    async def get(self, chat_id: int) -> ChatState | None:
        return self._states.get(chat_id)

    async def upsert(self, state: ChatState) -> None:
        self._states[state.chat_id] = state


async def test_describe_service_message_renders_chat_title_diff() -> None:
    service = ChatStateService(InMemoryChatStateRepository())
    await service.update_title(-1001, "Старое имя")
    actor = User(id=1, is_bot=False, first_name="Admin", username="admin")
    chat = Chat(id=-1001, type="supergroup", title="Старое имя")
    message = Message(
        message_id=10,
        date=datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc),
        chat=chat,
        from_user=actor,
        new_chat_title="Новое имя",
    )

    rendered = await describe_service_message(message=message, chat_state_service=service)

    assert rendered is not None
    assert "Старое имя" in rendered
    assert "Новое имя" in rendered
    assert 'https://t.me/c/1/10' in rendered


async def test_describe_service_message_renders_auto_delete_diff() -> None:
    service = ChatStateService(InMemoryChatStateRepository())
    await service.update_auto_delete_timer(-1001, 60)
    actor = User(id=1, is_bot=False, first_name="Admin")
    chat = Chat(id=-1001, type="supergroup", title="Chat")
    message = Message(
        message_id=11,
        date=datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc),
        chat=chat,
        from_user=actor,
        message_auto_delete_timer_changed=MessageAutoDeleteTimerChanged(message_auto_delete_time=300),
    )

    rendered = await describe_service_message(message=message, chat_state_service=service)

    assert rendered is not None
    assert "60 сек." in rendered
    assert "300 сек." in rendered
    assert 'https://t.me/c/1/11' in rendered
