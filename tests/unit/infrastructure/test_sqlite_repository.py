import aiosqlite

from app.domain.models import CustomCommand
from app.infrastructure.persistence import SQLiteCustomCommandRepository, SQLiteDatabase


async def test_sqlite_repository_persists_commands(tmp_path) -> None:
    database = SQLiteDatabase(tmp_path / "bot.db")
    await database.initialize()
    repository = SQLiteCustomCommandRepository(database)
    command = CustomCommand(
        normalized_name="команда",
        display_name="Команда",
        response_html="<b>Ответ</b>",
    )

    await repository.upsert(command)

    assert await repository.get_by_name("команда") == command
    assert await repository.list_commands() == [command]


async def test_sqlite_database_migrates_legacy_custom_commands_schema(tmp_path) -> None:
    database_path = tmp_path / "bot.db"

    async with aiosqlite.connect(database_path) as connection:
        await connection.execute(
            """
            CREATE TABLE custom_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL UNIQUE,
                text TEXT NOT NULL
            )
            """
        )
        await connection.execute(
            """
            INSERT INTO custom_commands (command, text)
            VALUES (?, ?)
            """,
            ("Привет", "<b>Мир</b>"),
        )
        await connection.commit()

    database = SQLiteDatabase(database_path)
    await database.initialize()
    repository = SQLiteCustomCommandRepository(database)

    migrated_command = await repository.get_by_name("привет")

    assert migrated_command is not None
    assert migrated_command.display_name == "Привет"
    assert migrated_command.response_html == "<b>Мир</b>"

