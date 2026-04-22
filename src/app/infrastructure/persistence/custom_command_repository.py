from time import perf_counter

from app.application.protocols import CustomCommandRepository
from app.domain.models import CustomCommand
from app.infrastructure.observability import log_step
from app.infrastructure.persistence.sqlite import SQLiteDatabase


class SQLiteCustomCommandRepository(CustomCommandRepository):
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    async def list_commands(self) -> list[CustomCommand]:
        started_at = perf_counter()
        with self._database.trace_operation("custom_commands.list"):
            async with self._database.connect() as connection:
                try:
                    cursor = await connection.execute(
                        """
                        SELECT normalized_name, display_name, response_html
                        FROM custom_commands
                        ORDER BY display_name COLLATE NOCASE
                        """
                    )
                    rows = list(await cursor.fetchall())
                    await cursor.close()
                except Exception:
                    self._database.observe_db_operation(
                        "custom_commands.list", "error", started_at
                    )
                    self._database.logger.exception("custom_commands_list_failed")
                    raise

        self._database.observe_db_operation(
            "custom_commands.list", "success", started_at
        )
        log_step(
            self._database.logger,
            "custom_commands_loaded",
            operation="custom_commands.list",
            row_count=len(rows),
        )

        return [
            CustomCommand(
                normalized_name=str(row["normalized_name"]),
                display_name=str(row["display_name"]),
                response_html=str(row["response_html"]),
            )
            for row in rows
        ]

    async def get_by_name(self, normalized_name: str) -> CustomCommand | None:
        started_at = perf_counter()
        with self._database.trace_operation("custom_commands.get"):
            async with self._database.connect() as connection:
                try:
                    cursor = await connection.execute(
                        """
                        SELECT normalized_name, display_name, response_html
                        FROM custom_commands
                        WHERE normalized_name = ?
                        """,
                        (normalized_name,),
                    )
                    row = await cursor.fetchone()
                    await cursor.close()
                except Exception:
                    self._database.observe_db_operation(
                        "custom_commands.get", "error", started_at
                    )
                    self._database.logger.exception(
                        "custom_command_get_failed",
                        extra={"command_name": normalized_name},
                    )
                    raise

        if row is None:
            self._database.observe_db_operation(
                "custom_commands.get", "success", started_at
            )
            return None

        self._database.observe_db_operation(
            "custom_commands.get", "success", started_at
        )
        return CustomCommand(
            normalized_name=str(row["normalized_name"]),
            display_name=str(row["display_name"]),
            response_html=str(row["response_html"]),
        )

    async def upsert(self, command: CustomCommand) -> None:
        started_at = perf_counter()
        with self._database.trace_operation("custom_commands.upsert"):
            async with self._database.connect() as connection:
                try:
                    await connection.execute(
                        """
                        INSERT INTO custom_commands (
                            normalized_name,
                            display_name,
                            response_html
                        )
                        VALUES (?, ?, ?)
                        ON CONFLICT(normalized_name) DO UPDATE SET
                            display_name = excluded.display_name,
                            response_html = excluded.response_html
                        """,
                        (
                            command.normalized_name,
                            command.display_name,
                            command.response_html,
                        ),
                    )
                    await connection.commit()
                except Exception:
                    self._database.observe_db_operation(
                        "custom_commands.upsert", "error", started_at
                    )
                    self._database.logger.exception(
                        "custom_command_upsert_failed",
                        extra={"command_name": command.normalized_name},
                    )
                    raise

        self._database.observe_db_operation(
            "custom_commands.upsert", "success", started_at
        )

    async def delete(self, normalized_name: str) -> bool:
        started_at = perf_counter()
        with self._database.trace_operation("custom_commands.delete"):
            async with self._database.connect() as connection:
                try:
                    cursor = await connection.execute(
                        """
                        DELETE FROM custom_commands
                        WHERE normalized_name = ?
                        """,
                        (normalized_name,),
                    )
                    await connection.commit()
                    deleted_rows = cursor.rowcount
                    await cursor.close()
                except Exception:
                    self._database.observe_db_operation(
                        "custom_commands.delete", "error", started_at
                    )
                    self._database.logger.exception(
                        "custom_command_delete_failed",
                        extra={"command_name": normalized_name},
                    )
                    raise

        self._database.observe_db_operation(
            "custom_commands.delete", "success", started_at
        )
        return deleted_rows > 0
