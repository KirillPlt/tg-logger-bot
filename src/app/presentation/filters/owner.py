from typing import Any

from aiogram.filters import BaseFilter


class OwnerFilter(BaseFilter):
    def __init__(self, owner_id: int) -> None:
        self._owner_id = owner_id

    async def __call__(self, event: Any) -> bool:
        user = getattr(event, "from_user", None)
        return user is not None and user.id == self._owner_id
