from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
import shutil

import aiosqlite

from app.domain.models import normalize_command_name, sanitize_command_name


CREATE_CUSTOM_COMMANDS_TABLE = """
CREATE TABLE IF NOT EXISTS custom_commands (
    normalized_name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    response_html TEXT NOT NULL
)
"""


class SQLiteDatabase:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._legacy_path = Path("bot.db")

    @property
    def path(self) -> Path:
        return self._path

    async def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate_legacy_path()

        async with self.connect() as connection:
            await self._migrate_custom_commands_table(connection)
            await connection.commit()

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[aiosqlite.Connection]:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = await aiosqlite.connect(self._path)
        connection.row_factory = aiosqlite.Row

        await connection.execute("PRAGMA foreign_keys = ON")
        await connection.execute("PRAGMA journal_mode = WAL")

        try:
            yield connection
        finally:
            await connection.close()

    def _migrate_legacy_path(self) -> None:
        if self._path == self._legacy_path:
            return

        if self._path.exists() or not self._legacy_path.exists():
            return

        shutil.copy2(self._legacy_path, self._path)

    async def _migrate_custom_commands_table(self, connection: aiosqlite.Connection) -> None:
        table_info_cursor = await connection.execute("PRAGMA table_info(custom_commands)")
        table_info = await table_info_cursor.fetchall()
        await table_info_cursor.close()

        if not table_info:
            await connection.execute(CREATE_CUSTOM_COMMANDS_TABLE)
            return

        column_names = {str(row["name"]) for row in table_info}
        expected_columns = {"normalized_name", "display_name", "response_html"}

        if column_names == expected_columns:
            return

        await connection.execute("ALTER TABLE custom_commands RENAME TO custom_commands_legacy")
        await connection.execute(CREATE_CUSTOM_COMMANDS_TABLE)

        legacy_rows_cursor = await connection.execute(
            """
            SELECT command, text
            FROM custom_commands_legacy
            """
        )
        legacy_rows = await legacy_rows_cursor.fetchall()
        await legacy_rows_cursor.close()

        for row in legacy_rows:
            display_name = sanitize_command_name(str(row["command"]))
            normalized_name = normalize_command_name(display_name)
            response_html = str(row["text"]).strip()

            if not response_html:
                continue

            await connection.execute(
                """
                INSERT OR REPLACE INTO custom_commands (
                    normalized_name,
                    display_name,
                    response_html
                )
                VALUES (?, ?, ?)
                """,
                (normalized_name, display_name, response_html),
            )

        await connection.execute("DROP TABLE custom_commands_legacy")
