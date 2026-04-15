from app.application.protocols import CustomCommandRepository
from app.domain.models import CustomCommand
from app.infrastructure.persistence.sqlite import SQLiteDatabase


class SQLiteCustomCommandRepository(CustomCommandRepository):
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    async def list_commands(self) -> list[CustomCommand]:
        async with self._database.connect() as connection:
            cursor = await connection.execute(
                """
                SELECT normalized_name, display_name, response_html
                FROM custom_commands
                ORDER BY display_name COLLATE NOCASE
                """
            )
            rows = await cursor.fetchall()
            await cursor.close()

        return [
            CustomCommand(
                normalized_name=str(row["normalized_name"]),
                display_name=str(row["display_name"]),
                response_html=str(row["response_html"]),
            )
            for row in rows
        ]

    async def get_by_name(self, normalized_name: str) -> CustomCommand | None:
        async with self._database.connect() as connection:
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

        if row is None:
            return None

        return CustomCommand(
            normalized_name=str(row["normalized_name"]),
            display_name=str(row["display_name"]),
            response_html=str(row["response_html"]),
        )

    async def upsert(self, command: CustomCommand) -> None:
        async with self._database.connect() as connection:
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

    async def delete(self, normalized_name: str) -> bool:
        async with self._database.connect() as connection:
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

        return deleted_rows > 0
