from dataclasses import dataclass
from datetime import timedelta

from app.application.protocols import Clock
from app.application.services import AdminAccessService, CustomCommandService
from app.config import Settings
from app.infrastructure.persistence import SQLiteCustomCommandRepository, SQLiteDatabase
from app.infrastructure.time import SystemClock


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    settings: Settings
    database: SQLiteDatabase
    clock: Clock
    custom_command_service: CustomCommandService
    admin_access_service: AdminAccessService


def build_container(settings: Settings) -> ApplicationContainer:
    database = SQLiteDatabase(settings.database.path)
    clock = SystemClock(settings.runtime.timezone)
    repository = SQLiteCustomCommandRepository(database)
    custom_command_service = CustomCommandService(repository)
    admin_access_service = AdminAccessService(
        main_chat_id=settings.bot.chat_id,
        clock=clock,
        cache_ttl=timedelta(seconds=settings.runtime.admin_cache_ttl_seconds),
    )

    return ApplicationContainer(
        settings=settings,
        database=database,
        clock=clock,
        custom_command_service=custom_command_service,
        admin_access_service=admin_access_service,
    )
