from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChatUser:
    id: int
    mention_html: str
    username: str | None = None

    @property
    def username_tag(self) -> str:
        return f" [@{self.username}]" if self.username else ""
