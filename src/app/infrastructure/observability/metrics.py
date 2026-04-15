from prometheus_client import Counter, Histogram, start_http_server


class MetricsCollector:
    def __init__(self) -> None:
        self.updates_total = Counter(
            "tg_logger_updates_total",
            "Telegram updates processed by the bot.",
            ("update_type", "status"),
        )
        self.update_duration_seconds = Histogram(
            "tg_logger_update_duration_seconds",
            "Duration of Telegram update processing.",
            ("update_type", "status"),
        )
        self.handler_events_total = Counter(
            "tg_logger_handler_events_total",
            "Handler-level events.",
            ("handler", "status"),
        )
        self.handler_duration_seconds = Histogram(
            "tg_logger_handler_duration_seconds",
            "Duration of handler and service operations.",
            ("handler", "status"),
        )
        self.telegram_actions_total = Counter(
            "tg_logger_telegram_actions_total",
            "Outgoing Telegram API actions executed by the bot.",
            ("action", "status"),
        )
        self.telegram_action_duration_seconds = Histogram(
            "tg_logger_telegram_action_duration_seconds",
            "Duration of outgoing Telegram API actions.",
            ("action", "status"),
        )
        self.db_operations_total = Counter(
            "tg_logger_db_operations_total",
            "Database operations executed by the bot.",
            ("operation", "status"),
        )
        self.db_operation_duration_seconds = Histogram(
            "tg_logger_db_operation_duration_seconds",
            "Duration of database operations.",
            ("operation", "status"),
        )
        self.business_events_total = Counter(
            "tg_logger_business_events_total",
            "Business-level events detected by the bot.",
            ("event_type",),
        )
        self.cache_events_total = Counter(
            "tg_logger_cache_events_total",
            "Cache hits and misses.",
            ("cache_name", "status"),
        )

    def observe_update(self, update_type: str, status: str, duration_seconds: float) -> None:
        self.updates_total.labels(update_type=update_type, status=status).inc()
        self.update_duration_seconds.labels(
            update_type=update_type,
            status=status,
        ).observe(duration_seconds)

    def observe_handler(self, handler: str, status: str, duration_seconds: float) -> None:
        self.handler_events_total.labels(handler=handler, status=status).inc()
        self.handler_duration_seconds.labels(handler=handler, status=status).observe(
            duration_seconds
        )

    def observe_telegram_action(self, action: str, status: str, duration_seconds: float) -> None:
        self.telegram_actions_total.labels(action=action, status=status).inc()
        self.telegram_action_duration_seconds.labels(action=action, status=status).observe(
            duration_seconds
        )

    def observe_db_operation(self, operation: str, status: str, duration_seconds: float) -> None:
        self.db_operations_total.labels(operation=operation, status=status).inc()
        self.db_operation_duration_seconds.labels(
            operation=operation,
            status=status,
        ).observe(duration_seconds)

    def observe_business_event(self, event_type: str) -> None:
        self.business_events_total.labels(event_type=event_type).inc()

    def observe_cache_event(self, cache_name: str, status: str) -> None:
        self.cache_events_total.labels(cache_name=cache_name, status=status).inc()

    def start_server(self, host: str, port: int) -> None:
        start_http_server(port=port, addr=host)
