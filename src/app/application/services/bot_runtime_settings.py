import asyncio
from dataclasses import replace
from time import perf_counter

from app.application.protocols import BotRuntimeSettingsRepository
from app.domain.models import BotRuntimeSettings
from app.infrastructure.observability import MetricsCollector, get_logger, log_step


class BotRuntimeSettingsService:
    def __init__(
        self,
        repository: BotRuntimeSettingsRepository,
        metrics: MetricsCollector | None = None,
    ) -> None:
        self._repository = repository
        self._metrics = metrics
        self._cached_settings: BotRuntimeSettings | None = None
        self._lock = asyncio.Lock()
        self._logger = get_logger(__name__)

    async def get(self) -> BotRuntimeSettings:
        await self._ensure_cache()
        if self._cached_settings is None:
            self._cached_settings = BotRuntimeSettings()
        return self._cached_settings

    async def is_reaction_logging_enabled(self) -> bool:
        settings = await self.get()
        return settings.reaction_logs_enabled

    async def get_greeting(self) -> str | None:
        settings = await self.get()
        return settings.greeting_html

    async def set_greeting(self, greeting_html: str) -> tuple[BotRuntimeSettings, bool]:
        started_at = perf_counter()
        cleaned_greeting = greeting_html.strip()
        if not cleaned_greeting:
            raise ValueError("Текст приветствия не может быть пустым.")

        current_settings = await self.get()
        was_changed = current_settings.greeting_html != cleaned_greeting
        updated_settings = replace(current_settings, greeting_html=cleaned_greeting)
        await self._repository.save(updated_settings)
        self._cached_settings = updated_settings

        if self._metrics is not None:
            if was_changed:
                self._metrics.observe_business_event("greeting_updated")
            self._metrics.observe_handler(
                handler="bot_runtime_settings_service.set_greeting",
                status="success" if was_changed else "unchanged",
                duration_seconds=perf_counter() - started_at,
            )

        log_step(
            self._logger,
            "greeting_setting_updated",
            handler="bot_runtime_settings_service.set_greeting",
            changed=was_changed,
        )
        return updated_settings, was_changed

    async def set_reaction_logging_enabled(
        self, enabled: bool
    ) -> tuple[BotRuntimeSettings, bool]:
        started_at = perf_counter()
        current_settings = await self.get()
        was_changed = current_settings.reaction_logs_enabled != enabled
        updated_settings = replace(current_settings, reaction_logs_enabled=enabled)
        await self._repository.save(updated_settings)
        self._cached_settings = updated_settings

        if self._metrics is not None:
            if was_changed:
                self._metrics.observe_business_event(
                    "reaction_logs_enabled" if enabled else "reaction_logs_disabled"
                )
            self._metrics.observe_handler(
                handler="bot_runtime_settings_service.set_reaction_logging_enabled",
                status="success" if was_changed else "unchanged",
                duration_seconds=perf_counter() - started_at,
            )

        log_step(
            self._logger,
            "reaction_logging_setting_updated",
            handler="bot_runtime_settings_service.set_reaction_logging_enabled",
            enabled=enabled,
            changed=was_changed,
        )
        return updated_settings, was_changed

    async def _ensure_cache(self) -> None:
        if self._cached_settings is not None:
            if self._metrics is not None:
                self._metrics.observe_cache_event("bot_runtime_settings", "hit")
            return

        if self._metrics is not None:
            self._metrics.observe_cache_event("bot_runtime_settings", "miss")

        async with self._lock:
            if self._cached_settings is not None:
                if self._metrics is not None:
                    self._metrics.observe_cache_event("bot_runtime_settings", "hit")
                return

            self._cached_settings = await self._repository.get()
            log_step(
                self._logger,
                "bot_runtime_settings_cache_primed",
                cache_name="bot_runtime_settings",
                reaction_logs_enabled=self._cached_settings.reaction_logs_enabled,
                has_greeting=self._cached_settings.greeting_html is not None,
            )
