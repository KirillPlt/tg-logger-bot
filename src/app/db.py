from typing import Any

import aiosqlite

DB_PATH = "bot.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS custom_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL UNIQUE,
                text TEXT NOT NULL
            )
            """
        )
        await db.commit()


async def save_custom_command(command_name: str, command_text: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO custom_commands (command, text)
            VALUES (?, ?)
            ON CONFLICT(command) DO UPDATE SET
                text = excluded.text
            """,
            (command_name, command_text),
        )
        await db.commit()


async def get_custom_command(command_name: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT text
            FROM custom_commands
            WHERE command = ?
            """,
            (command_name,),
        )
        row: tuple[Any, ...] | None = await cursor.fetchone()
        await cursor.close()

    if row is None:
        return None

    return str(row[0])


async def delete_custom_command(command_name: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            DELETE FROM custom_commands
            WHERE command = ?
            """,
            (command_name,),
        )
        await db.commit()
        deleted: int = cursor.rowcount
        await cursor.close()

    return deleted > 0