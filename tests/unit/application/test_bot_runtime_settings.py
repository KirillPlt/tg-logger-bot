from app.application.services import BotRuntimeSettingsService
from app.domain.models import BotRuntimeSettings


class InMemoryBotRuntimeSettingsRepository:
    def __init__(self) -> None:
        self._settings = BotRuntimeSettings()

    async def get(self) -> BotRuntimeSettings:
        return self._settings

    async def save(self, settings: BotRuntimeSettings) -> None:
        self._settings = settings


async def test_runtime_settings_enable_reaction_logs_by_default() -> None:
    service = BotRuntimeSettingsService(InMemoryBotRuntimeSettingsRepository())

    assert await service.is_reaction_logging_enabled() is True


async def test_runtime_settings_service_can_disable_and_enable_reaction_logs() -> None:
    service = BotRuntimeSettingsService(InMemoryBotRuntimeSettingsRepository())

    disabled_settings, disabled_changed = await service.set_reaction_logging_enabled(False)
    enabled_settings, enabled_changed = await service.set_reaction_logging_enabled(True)

    assert disabled_changed is True
    assert disabled_settings.reaction_logs_enabled is False
    assert enabled_changed is True
    assert enabled_settings.reaction_logs_enabled is True
    assert await service.is_reaction_logging_enabled() is True
