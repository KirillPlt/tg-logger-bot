from collections.abc import Mapping
from contextvars import Token
import contextvars


_LOG_CONTEXT: contextvars.ContextVar[dict[str, object]] = contextvars.ContextVar(
    "log_context",
    default={},
)


def get_log_context() -> dict[str, object]:
    return dict(_LOG_CONTEXT.get())


def set_log_context(**context: object) -> Token[dict[str, object]]:
    current_context = get_log_context()
    current_context.update(
        {key: value for key, value in context.items() if value is not None}
    )
    return _LOG_CONTEXT.set(current_context)


def update_log_context(context: Mapping[str, object]) -> Token[dict[str, object]]:
    return set_log_context(**dict(context))


def clear_log_context(token: Token[dict[str, object]]) -> None:
    _LOG_CONTEXT.reset(token)
