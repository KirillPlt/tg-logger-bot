from time import perf_counter

from app.application.protocols import ChatStateRepository
from app.domain.models import ChatState
from app.infrastructure.persistence.sqlite import SQLiteDatabase


class SQLiteChatStateRepository(ChatStateRepository):
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    async def get(self, chat_id: int) -> ChatState | None:
        started_at = perf_counter()
        with self._database.trace_operation("chat_state.get"):
            async with self._database.connect() as connection:
                try:
                    cursor = await connection.execute(
                        """
                        SELECT chat_id, title, photo_file_unique_id, auto_delete_time_seconds
                        FROM chat_states
                        WHERE chat_id = ?
                        """,
                        (chat_id,),
                    )
                    row = await cursor.fetchone()
                    await cursor.close()
                except Exception:
                    self._database.observe_db_operation(
                        "chat_state.get", "error", started_at
                    )
                    self._database.logger.exception(
                        "chat_state_get_failed", extra={"chat_id": chat_id}
                    )
                    raise

        self._database.observe_db_operation("chat_state.get", "success", started_at)

        if row is None:
            return None

        return ChatState(
            chat_id=int(row["chat_id"]),
            title=str(row["title"]) if row["title"] is not None else None,
            photo_file_unique_id=(
                str(row["photo_file_unique_id"])
                if row["photo_file_unique_id"] is not None
                else None
            ),
            auto_delete_time_seconds=(
                int(row["auto_delete_time_seconds"])
                if row["auto_delete_time_seconds"] is not None
                else None
            ),
        )

    async def upsert(self, state: ChatState) -> None:
        started_at = perf_counter()
        with self._database.trace_operation("chat_state.upsert"):
            async with self._database.connect() as connection:
                try:
                    await connection.execute(
                        """
                        INSERT INTO chat_states (
                            chat_id,
                            title,
                            photo_file_unique_id,
                            auto_delete_time_seconds
                        )
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(chat_id) DO UPDATE SET
                            title = excluded.title,
                            photo_file_unique_id = excluded.photo_file_unique_id,
                            auto_delete_time_seconds = excluded.auto_delete_time_seconds
                        """,
                        (
                            state.chat_id,
                            state.title,
                            state.photo_file_unique_id,
                            state.auto_delete_time_seconds,
                        ),
                    )
                    await connection.commit()
                except Exception:
                    self._database.observe_db_operation(
                        "chat_state.upsert", "error", started_at
                    )
                    self._database.logger.exception(
                        "chat_state_upsert_failed",
                        extra={"chat_id": state.chat_id},
                    )
                    raise

        self._database.observe_db_operation("chat_state.upsert", "success", started_at)
