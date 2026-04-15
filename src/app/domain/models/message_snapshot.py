from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MessageSnapshot:
    chat_id: int
    message_id: int
    content_type: str
    rendered_html: str | None

