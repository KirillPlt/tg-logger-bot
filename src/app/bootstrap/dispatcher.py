from aiogram import Dispatcher

from app.bootstrap.container import ApplicationContainer
from app.config import Settings
from app.presentation.middlewares import (
    MessageStateMiddleware,
    UpdateObservabilityMiddleware,
)
from app.presentation.routers import (
    create_custom_command_router,
    create_join_request_router,
    create_member_event_router,
    create_message_event_router,
    create_runtime_control_router,
    create_system_update_router,
    create_start_router,
)


def create_dispatcher(
    settings: Settings, container: ApplicationContainer
) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.workflow_data.update(
        {
            "clock": container.clock,
            "custom_command_service": container.custom_command_service,
            "note_service": container.note_service,
            "admin_access_service": container.admin_access_service,
            "bot_runtime_settings_service": container.bot_runtime_settings_service,
            "metrics": container.metrics,
        }
    )
    dispatcher.update.outer_middleware(
        UpdateObservabilityMiddleware(
            container.metrics,
            tracing_enabled=settings.tracing.enabled,
        )
    )
    message_state_middleware = MessageStateMiddleware(
        settings=settings,
        message_snapshot_service=container.message_snapshot_service,
        chat_state_service=container.chat_state_service,
    )
    dispatcher.message.outer_middleware(message_state_middleware)
    dispatcher.edited_message.outer_middleware(message_state_middleware)
    dispatcher.include_routers(
        create_start_router(settings),
        create_join_request_router(settings),
        create_system_update_router(settings),
        create_member_event_router(settings),
        create_message_event_router(settings),
        create_runtime_control_router(settings),
        create_custom_command_router(settings),
    )
    return dispatcher
