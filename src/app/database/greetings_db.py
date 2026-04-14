import aiosqlite


class GreetingsDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    async def init_db(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS greetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT NOT NULL UNIQUE,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.commit()

    async def get_greeting(self) -> str | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT text FROM greetings
                WHERE command = ?
                """,
                ("greetings",),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def add_greeting(self, text: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO greetings (text, command)
                VALUES (?, ?)
                ON CONFLICT(command) DO UPDATE SET
                    text = excluded.text
                    updated_at = CURRENT_TIMESTAMP
                """,
                (text, "greetings"),
            )
            await db.commit()

    async def remove_greeting(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM greetings
                WHERE command = ?
                """,
                ("greetings",),
            )
            await db.commit()
