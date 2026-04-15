import asyncio
from dataclasses import dataclass

from app.application.protocols import CustomCommandRepository
from app.domain.models import CustomCommand, normalize_command_name, sanitize_command_name


@dataclass(frozen=True, slots=True)
class SaveCommandResult:
    command: CustomCommand
    was_created: bool


class CustomCommandService:
    def __init__(self, repository: CustomCommandRepository) -> None:
        self._repository = repository
        self._cache: dict[str, CustomCommand] = {}
        self._cache_ready = False
        self._lock = asyncio.Lock()

    async def prime_cache(self) -> None:
        await self._ensure_cache()

    async def list_commands(self) -> tuple[CustomCommand, ...]:
        await self._ensure_cache()
        return tuple(
            sorted(self._cache.values(), key=lambda command: command.display_name.casefold())
        )

    async def resolve(self, raw_name: str) -> CustomCommand | None:
        normalized_name = normalize_command_name(raw_name)
        await self._ensure_cache()
        return self._cache.get(normalized_name)

    async def save(self, raw_name: str, response_html: str) -> SaveCommandResult:
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
        return SaveCommandResult(command=command, was_created=was_created)

    async def delete(self, raw_name: str) -> bool:
        normalized_name = normalize_command_name(raw_name)
        await self._ensure_cache()

        was_deleted = await self._repository.delete(normalized_name)
        if was_deleted:
            self._cache.pop(normalized_name, None)

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
