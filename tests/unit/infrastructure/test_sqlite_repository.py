import aiosqlite

from app.domain.models import BotRuntimeSettings, CustomCommand, SavedNote
from app.infrastructure.persistence import (
    SQLiteBotRuntimeSettingsRepository,
    SQLiteCustomCommandRepository,
    SQLiteDatabase,
    SQLiteNoteRepository,
)


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


async def test_sqlite_repository_persists_runtime_settings(tmp_path) -> None:
    database = SQLiteDatabase(tmp_path / "bot.db")
    await database.initialize()
    repository = SQLiteBotRuntimeSettingsRepository(database)

    default_settings = await repository.get()
    assert default_settings.reaction_logs_enabled is True

    await repository.save(
        BotRuntimeSettings(
            reaction_logs_enabled=False,
            greeting_html="<b>Привет!</b>",
        )
    )

    updated_settings = await repository.get()
    assert updated_settings.reaction_logs_enabled is False
    assert updated_settings.greeting_html == "<b>Привет!</b>"


async def test_sqlite_repository_persists_notes(tmp_path) -> None:
    database = SQLiteDatabase(tmp_path / "bot.db")
    await database.initialize()
    repository = SQLiteNoteRepository(database)
    note = SavedNote(
        normalized_name="наказание",
        display_name="Наказание",
        response_html="<b>Описание</b>",
    )

    await repository.upsert(note)

    assert await repository.get_by_name("наказание") == note
    assert await repository.list_notes() == [note]


async def test_sqlite_database_migrates_runtime_settings_greeting_column(
    tmp_path,
) -> None:
    database_path = tmp_path / "bot.db"

    async with aiosqlite.connect(database_path) as connection:
        await connection.execute(
            """
            CREATE TABLE bot_runtime_settings (
                singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                reaction_logs_enabled INTEGER NOT NULL DEFAULT 1 CHECK (reaction_logs_enabled IN (0, 1))
            )
            """
        )
        await connection.execute(
            """
            INSERT INTO bot_runtime_settings (singleton_id, reaction_logs_enabled)
            VALUES (1, 1)
            """
        )
        await connection.commit()

    database = SQLiteDatabase(database_path)
    await database.initialize()
    repository = SQLiteBotRuntimeSettingsRepository(database)

    await repository.save(
        BotRuntimeSettings(reaction_logs_enabled=True, greeting_html="hello")
    )
    updated_settings = await repository.get()

    assert updated_settings.greeting_html == "hello"
