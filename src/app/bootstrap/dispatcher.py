from aiogram import Dispatcher

from app.bootstrap.container import ApplicationContainer
from app.config import Settings
from app.presentation.routers import (
    create_custom_command_router,
    create_join_request_router,
    create_member_event_router,
    create_message_event_router,
    create_start_router,
)


def create_dispatcher(settings: Settings, container: ApplicationContainer) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.workflow_data.update(
        {
            "clock": container.clock,
            "custom_command_service": container.custom_command_service,
            "admin_access_service": container.admin_access_service,
        }
    )
    dispatcher.include_routers(
        create_start_router(settings),
        create_join_request_router(settings),
        create_member_event_router(settings),
        create_message_event_router(settings),
        create_custom_command_router(settings),
    )
    return dispatcher
