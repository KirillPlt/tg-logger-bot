from dataclasses import dataclass, field
from datetime import datetime, timedelta

from aiogram import Bot

from app.application.protocols import Clock


@dataclass(slots=True)
class AdminAccessService:
    main_chat_id: int
    clock: Clock
    cache_ttl: timedelta
    _cached_admin_ids: set[int] = field(init=False, default_factory=set)
    _cache_expires_at: datetime | None = field(init=False, default=None)

    async def is_chat_admin(self, bot: Bot, user_id: int) -> bool:
        now = self.clock.now()

        if self._cache_expires_at is None or now >= self._cache_expires_at:
            administrators = await bot.get_chat_administrators(self.main_chat_id)
            self._cached_admin_ids = {member.user.id for member in administrators}
            self._cache_expires_at = now + self.cache_ttl

        return user_id in self._cached_admin_ids
