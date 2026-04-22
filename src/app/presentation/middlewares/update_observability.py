from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import nullcontext
from time import perf_counter
from uuid import uuid4

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from app.infrastructure.observability import (
    MetricsCollector,
    clear_log_context,
    get_trace_log_context,
    get_logger,
    log_step,
    mark_span_failed,
    set_log_context,
    start_update_span,
)


class UpdateObservabilityMiddleware(BaseMiddleware):
    def __init__(
        self, metrics: MetricsCollector, tracing_enabled: bool = False
    ) -> None:
        self._metrics = metrics
        self._tracing_enabled = tracing_enabled
        self._logger = get_logger(__name__)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, object]], Awaitable[object]],
        event: TelegramObject,
        data: dict[str, object],
    ) -> object:
        if not isinstance(event, Update):
            return await handler(event, data)

        update_type = self._resolve_update_type(event)
        span_context = (
            start_update_span(event.update_id, update_type)
            if self._tracing_enabled
            else nullcontext()
        )

        with span_context as span:
            context_fields: dict[str, object] = {
                "update_id": event.update_id,
                "update_type": update_type,
            }
            trace_context = get_trace_log_context() if self._tracing_enabled else {}
            if trace_context:
                context_fields.update(trace_context)
            else:
                context_fields["trace_id"] = uuid4().hex

            context_token = set_log_context(**context_fields)
            started_at = perf_counter()

            log_step(
                self._logger,
                "update_received",
                update_type=update_type,
                update_id=event.update_id,
            )

            try:
                result = await handler(event, data)
            except Exception as error:
                duration_seconds = perf_counter() - started_at
                self._metrics.observe_update(update_type, "error", duration_seconds)
                if span is not None:
                    mark_span_failed(span, error)
                log_step(
                    self._logger,
                    "update_failed",
                    level=40,
                    update_type=update_type,
                    duration_ms=round(duration_seconds * 1000, 3),
                )
                self._logger.exception("update_processing_failed")
                raise
            else:
                duration_seconds = perf_counter() - started_at
                self._metrics.observe_update(update_type, "success", duration_seconds)
                log_step(
                    self._logger,
                    "update_finished",
                    update_type=update_type,
                    duration_ms=round(duration_seconds * 1000, 3),
                )
                return result
            finally:
                clear_log_context(context_token)

    @staticmethod
    def _resolve_update_type(update: Update) -> str:
        for field_name, value in update.model_dump(exclude_none=False).items():
            if field_name == "update_id":
                continue
            if value is not None:
                return field_name
        return "unknown"
