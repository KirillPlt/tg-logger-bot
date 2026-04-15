from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChatState:
    chat_id: int
    title: str | None = None
    photo_file_unique_id: str | None = None
    auto_delete_time_seconds: int | None = None

