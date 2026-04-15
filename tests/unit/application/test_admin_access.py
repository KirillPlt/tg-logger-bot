from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.application.services import AdminAccessService


class FakeClock:
    def __init__(self) -> None:
        self._now = datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


class FakeBot:
    def __init__(self, admin_ids: set[int]) -> None:
        self._admin_ids = admin_ids
        self.calls = 0

    async def get_chat_administrators(self, _: int) -> list[SimpleNamespace]:
        self.calls += 1
        return [
            SimpleNamespace(user=SimpleNamespace(id=admin_id))
            for admin_id in self._admin_ids
        ]


async def test_admin_access_service_uses_ttl_cache() -> None:
    clock = FakeClock()
    service = AdminAccessService(
        main_chat_id=-1001234567890,
        clock=clock,
        cache_ttl=timedelta(seconds=60),
    )
    bot = FakeBot({1, 2, 3})

    assert await service.is_chat_admin(bot, 1) is True
    assert await service.is_chat_admin(bot, 999) is False
    assert bot.calls == 1

    clock.advance(timedelta(seconds=30))
    assert await service.is_chat_admin(bot, 2) is True
    assert bot.calls == 1

    clock.advance(timedelta(seconds=31))
    assert await service.is_chat_admin(bot, 3) is True
    assert bot.calls == 2

