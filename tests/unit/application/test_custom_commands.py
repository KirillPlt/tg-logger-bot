from app.application.services import CustomCommandService
from app.domain.models import CustomCommand


class InMemoryCommandRepository:
    def __init__(self) -> None:
        self._commands: dict[str, CustomCommand] = {}

    async def list_commands(self) -> list[CustomCommand]:
        return list(self._commands.values())

    async def get_by_name(self, normalized_name: str) -> CustomCommand | None:
        return self._commands.get(normalized_name)

    async def upsert(self, command: CustomCommand) -> None:
        self._commands[command.normalized_name] = command

    async def delete(self, normalized_name: str) -> bool:
        return self._commands.pop(normalized_name, None) is not None


async def test_save_command_creates_case_insensitive_entry() -> None:
    service = CustomCommandService(InMemoryCommandRepository())

    result = await service.save("  Привет Мир  ", "<b>Ответ</b>")

    assert result.was_created is True
    assert result.command.display_name == "Привет Мир"
    assert result.command.normalized_name == "привет мир"
    assert (await service.resolve("привет МИР")) == result.command


async def test_save_command_updates_existing_entry() -> None:
    service = CustomCommandService(InMemoryCommandRepository())
    await service.save("Команда", "Первая версия")

    result = await service.save("  команда ", "Вторая версия")

    assert result.was_created is False
    assert result.command.response_html == "Вторая версия"
    assert len(await service.list_commands()) == 1


async def test_delete_command_removes_cached_entry() -> None:
    service = CustomCommandService(InMemoryCommandRepository())
    await service.save("Команда", "Текст")

    was_deleted = await service.delete("команда")

    assert was_deleted is True
    assert await service.resolve("Команда") is None

