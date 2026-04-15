from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import shutil
from time import perf_counter

import aiosqlite

from app.domain.models import normalize_command_name, sanitize_command_name
from app.infrastructure.observability import MetricsCollector, get_logger, log_step


CREATE_CUSTOM_COMMANDS_TABLE = """
CREATE TABLE IF NOT EXISTS custom_commands (
    normalized_name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    response_html TEXT NOT NULL
)
"""

CREATE_MESSAGE_SNAPSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS message_snapshots (
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    rendered_html TEXT NULL,
    PRIMARY KEY (chat_id, message_id)
)
"""

CREATE_CHAT_STATES_TABLE = """
CREATE TABLE IF NOT EXISTS chat_states (
    chat_id INTEGER PRIMARY KEY,
    title TEXT NULL,
    photo_file_unique_id TEXT NULL,
    auto_delete_time_seconds INTEGER NULL
)
"""

CREATE_BOT_RUNTIME_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS bot_runtime_settings (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    reaction_logs_enabled INTEGER NOT NULL DEFAULT 1 CHECK (reaction_logs_enabled IN (0, 1))
)
"""


class SQLiteDatabase:
    def __init__(self, path: Path, metrics: MetricsCollector | None = None) -> None:
        self._path = Path(path)
        self._legacy_path = Path("bot.db")
        self._metrics = metrics
        self._logger = get_logger(__name__)

    @property
    def path(self) -> Path:
        return self._path

    async def initialize(self) -> None:
        operation_started_at = perf_counter()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate_legacy_path()

        try:
            async with self.connect() as connection:
                await self._migrate_custom_commands_table(connection)
                await connection.execute(CREATE_MESSAGE_SNAPSHOTS_TABLE)
                await connection.execute(CREATE_CHAT_STATES_TABLE)
                await connection.execute(CREATE_BOT_RUNTIME_SETTINGS_TABLE)
                await connection.execute(
                    """
                    INSERT OR IGNORE INTO bot_runtime_settings (
                        singleton_id,
                        reaction_logs_enabled
                    )
                    VALUES (1, 1)
                    """
                )
                await connection.commit()
        except Exception:
            self._observe_operation("initialize_database", "error", operation_started_at)
            self._logger.exception(
                "database_initialize_failed",
                extra={"operation": "initialize_database", "db_path": str(self._path)},
            )
            raise

        self._observe_operation("initialize_database", "success", operation_started_at)
        log_step(
            self._logger,
            "database_initialized",
            operation="initialize_database",
            db_path=str(self._path),
        )

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
        log_step(
            self._logger,
            "legacy_database_copied",
            operation="copy_legacy_database",
            source=str(self._legacy_path),
            destination=str(self._path),
        )

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
        legacy_rows = list(await legacy_rows_cursor.fetchall())
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
        log_step(
            self._logger,
            "legacy_custom_commands_migrated",
            operation="migrate_custom_commands",
            migrated_rows=len(legacy_rows),
        )

    def observe_db_operation(
        self,
        operation: str,
        status: str,
        started_at: float,
    ) -> None:
        self._observe_operation(operation, status, started_at)

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def _observe_operation(
        self,
        operation: str,
        status: str,
        started_at: float,
    ) -> None:
        if self._metrics is None:
            return

        self._metrics.observe_db_operation(
            operation=operation,
            status=status,
            duration_seconds=perf_counter() - started_at,
        )
