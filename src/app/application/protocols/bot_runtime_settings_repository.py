from typing import Protocol

from app.domain.models import BotRuntimeSettings


class BotRuntimeSettingsRepository(Protocol):
    async def get(self) -> BotRuntimeSettings: ...

    async def save(self, settings: BotRuntimeSettings) -> None: ...
