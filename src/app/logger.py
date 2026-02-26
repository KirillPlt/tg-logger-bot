import logging
from collections.abc import Sequence
from enum import Enum, auto
from typing import Any, Self

import structlog
from pydantic import TypeAdapter
from ecs_logging import StructlogFormatter
from structlog import make_filtering_bound_logger
from structlog.contextvars import bind_contextvars, merge_contextvars
from structlog.processors import (
    CallsiteParameter,
    CallsiteParameterAdder,
    format_exc_info,
    add_log_level,
    StackInfoRenderer,
    TimeStamper,
)
from structlog.stdlib import ExtraAdder, LoggerFactory, ProcessorFormatter

_type_adapter = TypeAdapter(Any)


def _pydantic_processor(_, __, event: dict) -> dict:
    return _type_adapter.dump_python(event, mode="json")


class LogSetupPreset(Enum):
    DEV_CONSOLE = auto()
    DEV_JSON = auto()
    PRODUCTION = auto()


class IwfLogger:
    __configured: bool = False

    __cs_params_dev_full = [
        CallsiteParameter.LINENO,
        CallsiteParameter.FUNC_NAME,
        CallsiteParameter.MODULE,
        CallsiteParameter.FILENAME,
        CallsiteParameter.THREAD_NAME,
        CallsiteParameter.THREAD,
        CallsiteParameter.PROCESS_NAME,
        CallsiteParameter.PROCESS,
    ]

    __cs_params_dev_minimal = [
        CallsiteParameter.MODULE,
        CallsiteParameter.FUNC_NAME,
        CallsiteParameter.LINENO,
    ]

    __cs_params_production = [
        CallsiteParameter.PROCESS,
        CallsiteParameter.PROCESS_NAME,
        CallsiteParameter.THREAD,
        CallsiteParameter.THREAD_NAME,
        CallsiteParameter.MODULE,
        CallsiteParameter.FUNC_NAME,
    ]

    @staticmethod
    def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
        return structlog.stdlib.get_logger(name)

    @staticmethod
    def __json_formatter(cs_params: Sequence[CallsiteParameter]) -> ProcessorFormatter:
        return ProcessorFormatter(
            foreign_pre_chain=(
                merge_contextvars,
                ExtraAdder(),
            ),
            processors=(
                ProcessorFormatter.remove_processors_meta,
                format_exc_info,
                merge_contextvars,
                CallsiteParameterAdder(cs_params),
                _pydantic_processor,
                StructlogFormatter(),
            ),
        )

    @staticmethod
    def __console_dev_formatter(
        cs_params: Sequence[CallsiteParameter], utc_tz: bool
    ) -> ProcessorFormatter:
        return ProcessorFormatter(
            foreign_pre_chain=(
                merge_contextvars,
                ExtraAdder(),
            ),
            processors=(
                ProcessorFormatter.remove_processors_meta,
                merge_contextvars,
                add_log_level,
                StackInfoRenderer(),
                structlog.dev.set_exc_info,
                CallsiteParameterAdder(cs_params),
                TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=utc_tz),
                structlog.dev.ConsoleRenderer(
                    level_styles={
                        "notset": structlog.dev.RED_BACK,
                        "debug": structlog.dev.CYAN,
                        "info": structlog.dev.BRIGHT,
                        "error": structlog.dev.RED,
                        "warning": structlog.dev.YELLOW,
                        "critical": structlog.dev.RED_BACK,
                    }
                ),
            ),
        )

    @staticmethod
    def __setup_logging(formatter: ProcessorFormatter, log_level: str) -> None:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(log_level)

    @classmethod
    def setup(
        cls,
        log_level: str,
        preset: LogSetupPreset = LogSetupPreset.DEV_CONSOLE,
        utc_tz: bool = False,
        **kwargs: Any,
    ) -> Self:
        if cls.__configured:
            return cls()

        formatter = None
        match preset:
            case LogSetupPreset.DEV_CONSOLE:
                cs_params = cls.__cs_params_dev_full
                formatter = cls.__console_dev_formatter(cs_params, utc_tz)
            case LogSetupPreset.DEV_JSON:
                cs_params = cls.__cs_params_dev_full
                formatter = cls.__json_formatter(cs_params)
            case LogSetupPreset.PRODUCTION:
                cs_params = cls.__cs_params_production
                formatter = cls.__json_formatter(cs_params)
            case _:
                raise ValueError("Invalid value for LogSetupPreset")

        cls.__setup_logging(formatter, log_level)

        structlog.configure(
            processors=(
                merge_contextvars,
                ProcessorFormatter.wrap_for_formatter,
            ),
            wrapper_class=make_filtering_bound_logger(log_level),
            logger_factory=LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        bind_contextvars(**kwargs)
        cls.__configured = True

        return cls()


get_logger = IwfLogger.get_logger

__all__ = ["IwfLogger", "LogSetupPreset", "get_logger"]