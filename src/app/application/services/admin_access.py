from dataclasses import dataclass, field
from datetime import datetime, timedelta
from time import perf_counter

from aiogram import Bot

from app.application.protocols import Clock
from app.infrastructure.observability import MetricsCollector, get_logger, log_step


@dataclass(slots=True)
class AdminAccessService:
    main_chat_id: int
    clock: Clock
    cache_ttl: timedelta
    metrics: MetricsCollector | None = None
    _cached_admin_ids: set[int] = field(init=False, default_factory=set)
    _cache_expires_at: datetime | None = field(init=False, default=None)
    _logger = get_logger(__name__)

    async def is_chat_admin(self, bot: Bot, user_id: int) -> bool:
        started_at = perf_counter()
        now = self.clock.now()

        if self._cache_expires_at is None or now >= self._cache_expires_at:
            administrators = await bot.get_chat_administrators(self.main_chat_id)
            self._cached_admin_ids = {member.user.id for member in administrators}
            self._cache_expires_at = now + self.cache_ttl
            if self.metrics is not None:
                self.metrics.observe_cache_event("admin_access", "miss")
            log_step(
                self._logger,
                "admin_cache_refreshed",
                cache_name="admin_access",
                admin_count=len(self._cached_admin_ids),
            )
        elif self.metrics is not None:
            self.metrics.observe_cache_event("admin_access", "hit")

        is_admin = user_id in self._cached_admin_ids
        if self.metrics is not None:
            self.metrics.observe_handler(
                handler="admin_access_service.is_chat_admin",
                status="success",
                duration_seconds=perf_counter() - started_at,
            )
        log_step(
            self._logger,
            "admin_access_checked",
            handler="admin_access_service.is_chat_admin",
            actor_user_id=user_id,
            is_admin=is_admin,
        )
        return is_admin
