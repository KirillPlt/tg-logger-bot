from time import perf_counter

from app.application.protocols import MessageSnapshotRepository
from app.domain.models import MessageSnapshot
from app.infrastructure.persistence.sqlite import SQLiteDatabase


class SQLiteMessageSnapshotRepository(MessageSnapshotRepository):
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    async def get(self, chat_id: int, message_id: int) -> MessageSnapshot | None:
        started_at = perf_counter()
        async with self._database.connect() as connection:
            try:
                cursor = await connection.execute(
                    """
                    SELECT chat_id, message_id, content_type, rendered_html
                    FROM message_snapshots
                    WHERE chat_id = ? AND message_id = ?
                    """,
                    (chat_id, message_id),
                )
                row = await cursor.fetchone()
                await cursor.close()
            except Exception:
                self._database.observe_db_operation("message_snapshot.get", "error", started_at)
                self._database.logger.exception(
                    "message_snapshot_get_failed",
                    extra={"chat_id": chat_id, "message_id": message_id},
                )
                raise

        if row is None:
            self._database.observe_db_operation("message_snapshot.get", "success", started_at)
            return None

        self._database.observe_db_operation("message_snapshot.get", "success", started_at)
        return MessageSnapshot(
            chat_id=int(row["chat_id"]),
            message_id=int(row["message_id"]),
            content_type=str(row["content_type"]),
            rendered_html=str(row["rendered_html"]) if row["rendered_html"] is not None else None,
        )

    async def upsert(self, snapshot: MessageSnapshot) -> None:
        started_at = perf_counter()
        async with self._database.connect() as connection:
            try:
                await connection.execute(
                    """
                    INSERT INTO message_snapshots (
                        chat_id,
                        message_id,
                        content_type,
                        rendered_html
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(chat_id, message_id) DO UPDATE SET
                        content_type = excluded.content_type,
                        rendered_html = excluded.rendered_html
                    """,
                    (
                        snapshot.chat_id,
                        snapshot.message_id,
                        snapshot.content_type,
                        snapshot.rendered_html,
                    ),
                )
                await connection.commit()
            except Exception:
                self._database.observe_db_operation("message_snapshot.upsert", "error", started_at)
                self._database.logger.exception(
                    "message_snapshot_upsert_failed",
                    extra={"chat_id": snapshot.chat_id, "message_id": snapshot.message_id},
                )
                raise

        self._database.observe_db_operation("message_snapshot.upsert", "success", started_at)
