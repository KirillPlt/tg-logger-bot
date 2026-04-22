from dataclasses import dataclass
from datetime import timedelta

from app.application.protocols import Clock
from app.application.services import (
    AdminAccessService,
    BotRuntimeSettingsService,
    ChatStateService,
    CustomCommandService,
    MessageSnapshotService,
    NoteService,
)
from app.config import Settings
from app.infrastructure.observability import MetricsCollector
from app.infrastructure.persistence import (
    SQLiteBotRuntimeSettingsRepository,
    SQLiteChatStateRepository,
    SQLiteCustomCommandRepository,
    SQLiteDatabase,
    SQLiteMessageSnapshotRepository,
    SQLiteNoteRepository,
)
from app.infrastructure.time import SystemClock


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    settings: Settings
    database: SQLiteDatabase
    clock: Clock
    metrics: MetricsCollector
    custom_command_service: CustomCommandService
    note_service: NoteService
    admin_access_service: AdminAccessService
    bot_runtime_settings_service: BotRuntimeSettingsService
    message_snapshot_service: MessageSnapshotService
    chat_state_service: ChatStateService


def build_container(settings: Settings) -> ApplicationContainer:
    metrics = MetricsCollector()
    database = SQLiteDatabase(settings.database.path, metrics=metrics)
    clock = SystemClock(settings.runtime.timezone)
    custom_command_repository = SQLiteCustomCommandRepository(database)
    note_repository = SQLiteNoteRepository(database)
    bot_runtime_settings_repository = SQLiteBotRuntimeSettingsRepository(database)
    message_snapshot_repository = SQLiteMessageSnapshotRepository(database)
    chat_state_repository = SQLiteChatStateRepository(database)
    custom_command_service = CustomCommandService(
        custom_command_repository, metrics=metrics
    )
    note_service = NoteService(note_repository, metrics=metrics)
    bot_runtime_settings_service = BotRuntimeSettingsService(
        bot_runtime_settings_repository,
        metrics=metrics,
    )
    admin_access_service = AdminAccessService(
        main_chat_id=settings.bot.chat_id,
        clock=clock,
        cache_ttl=timedelta(seconds=settings.runtime.admin_cache_ttl_seconds),
        metrics=metrics,
    )
    message_snapshot_service = MessageSnapshotService(message_snapshot_repository)
    chat_state_service = ChatStateService(chat_state_repository)

    return ApplicationContainer(
        settings=settings,
        database=database,
        clock=clock,
        metrics=metrics,
        custom_command_service=custom_command_service,
        note_service=note_service,
        admin_access_service=admin_access_service,
        bot_runtime_settings_service=bot_runtime_settings_service,
        message_snapshot_service=message_snapshot_service,
        chat_state_service=chat_state_service,
    )
