from time import perf_counter

from app.application.protocols import BotRuntimeSettingsRepository
from app.domain.models import BotRuntimeSettings
from app.infrastructure.persistence.sqlite import SQLiteDatabase


class SQLiteBotRuntimeSettingsRepository(BotRuntimeSettingsRepository):
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    async def get(self) -> BotRuntimeSettings:
        started_at = perf_counter()
        with self._database.trace_operation("bot_runtime_settings.get"):
            async with self._database.connect() as connection:
                try:
                    cursor = await connection.execute(
                        """
                        SELECT reaction_logs_enabled, greeting_html
                        FROM bot_runtime_settings
                        WHERE singleton_id = 1
                        """
                    )
                    row = await cursor.fetchone()
                    await cursor.close()
                except Exception:
                    self._database.observe_db_operation(
                        "bot_runtime_settings.get", "error", started_at
                    )
                    self._database.logger.exception("bot_runtime_settings_get_failed")
                    raise

        self._database.observe_db_operation(
            "bot_runtime_settings.get", "success", started_at
        )

        if row is None:
            return BotRuntimeSettings()

        greeting_html = row["greeting_html"]
        return BotRuntimeSettings(
            reaction_logs_enabled=bool(int(row["reaction_logs_enabled"])),
            greeting_html=str(greeting_html) if greeting_html is not None else None,
        )

    async def save(self, settings: BotRuntimeSettings) -> None:
        started_at = perf_counter()
        with self._database.trace_operation("bot_runtime_settings.save"):
            async with self._database.connect() as connection:
                try:
                    await connection.execute(
                        """
                        INSERT INTO bot_runtime_settings (
                            singleton_id,
                            reaction_logs_enabled,
                            greeting_html
                        )
                        VALUES (1, ?, ?)
                        ON CONFLICT(singleton_id) DO UPDATE SET
                            reaction_logs_enabled = excluded.reaction_logs_enabled,
                            greeting_html = excluded.greeting_html
                        """,
                        (
                            1 if settings.reaction_logs_enabled else 0,
                            settings.greeting_html,
                        ),
                    )
                    await connection.commit()
                except Exception:
                    self._database.observe_db_operation(
                        "bot_runtime_settings.save", "error", started_at
                    )
                    self._database.logger.exception(
                        "bot_runtime_settings_save_failed",
                        extra={
                            "reaction_logs_enabled": settings.reaction_logs_enabled,
                            "has_greeting": settings.greeting_html is not None,
                        },
                    )
                    raise

        self._database.observe_db_operation(
            "bot_runtime_settings.save", "success", started_at
        )
