import asyncio
from dataclasses import dataclass
from time import perf_counter

from app.application.protocols import CustomCommandRepository
from app.domain.models import CustomCommand, normalize_command_name, sanitize_command_name
from app.infrastructure.observability import MetricsCollector, get_logger, log_step


@dataclass(frozen=True, slots=True)
class SaveCommandResult:
    command: CustomCommand
    was_created: bool


class CustomCommandService:
    def __init__(
        self,
        repository: CustomCommandRepository,
        metrics: MetricsCollector | None = None,
    ) -> None:
        self._repository = repository
        self._metrics = metrics
        self._cache: dict[str, CustomCommand] = {}
        self._cache_ready = False
        self._lock = asyncio.Lock()
        self._logger = get_logger(__name__)

    async def prime_cache(self) -> None:
        await self._ensure_cache()

    async def list_commands(self) -> tuple[CustomCommand, ...]:
        await self._ensure_cache()
        return tuple(
            sorted(self._cache.values(), key=lambda command: command.display_name.casefold())
        )

    async def resolve(self, raw_name: str) -> CustomCommand | None:
        started_at = perf_counter()
        normalized_name = normalize_command_name(raw_name)
        await self._ensure_cache()
        command = self._cache.get(normalized_name)
        if self._metrics is not None:
            self._metrics.observe_cache_event(
                "custom_commands",
                "hit" if command is not None else "miss",
            )
            self._metrics.observe_handler(
                handler="custom_command_service.resolve",
                status="success",
                duration_seconds=perf_counter() - started_at,
            )
        log_step(
            self._logger,
            "custom_command_resolved",
            handler="custom_command_service.resolve",
            command_name=normalized_name,
            found=command is not None,
        )
        return command

    async def save(self, raw_name: str, response_html: str) -> SaveCommandResult:
        started_at = perf_counter()
        sanitized_name = sanitize_command_name(raw_name)
        normalized_name = normalize_command_name(sanitized_name)
        cleaned_response = response_html.strip()

        if not cleaned_response:
            raise ValueError("Текст команды не может быть пустым.")

        await self._ensure_cache()

        command = CustomCommand(
            normalized_name=normalized_name,
            display_name=sanitized_name,
            response_html=cleaned_response,
        )
        was_created = normalized_name not in self._cache

        await self._repository.upsert(command)
        self._cache[normalized_name] = command
        if self._metrics is not None:
            self._metrics.observe_business_event(
                "custom_command_created" if was_created else "custom_command_updated"
            )
            self._metrics.observe_handler(
                handler="custom_command_service.save",
                status="success",
                duration_seconds=perf_counter() - started_at,
            )
        log_step(
            self._logger,
            "custom_command_saved",
            handler="custom_command_service.save",
            command_name=normalized_name,
            was_created=was_created,
        )
        return SaveCommandResult(command=command, was_created=was_created)

    async def delete(self, raw_name: str) -> bool:
        started_at = perf_counter()
        normalized_name = normalize_command_name(raw_name)
        await self._ensure_cache()

        was_deleted = await self._repository.delete(normalized_name)
        if was_deleted:
            self._cache.pop(normalized_name, None)
            if self._metrics is not None:
                self._metrics.observe_business_event("custom_command_deleted")

        if self._metrics is not None:
            self._metrics.observe_handler(
                handler="custom_command_service.delete",
                status="success",
                duration_seconds=perf_counter() - started_at,
            )
        log_step(
            self._logger,
            "custom_command_deleted",
            handler="custom_command_service.delete",
            command_name=normalized_name,
            deleted=was_deleted,
        )

        return was_deleted

    async def _ensure_cache(self) -> None:
        if self._cache_ready:
            return

        async with self._lock:
            if self._cache_ready:
                return

            commands = await self._repository.list_commands()
            self._cache = {
                command.normalized_name: command
                for command in commands
            }
            self._cache_ready = True
            log_step(
                self._logger,
                "custom_command_cache_primed",
                cache_name="custom_commands",
                command_count=len(self._cache),
            )
