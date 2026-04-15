from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from aiogram.enums import ChatMemberStatus

from app.application.dto import ChatUser
from app.presentation.formatters import (
    build_chat_deep_link,
    describe_restricted_rights_changes,
    format_user_left_message,
    format_user_restricted_message,
)


def test_build_chat_deep_link_removes_telegram_prefix() -> None:
    assert build_chat_deep_link(-1001234567890) == "tg://chat?id=1234567890"


def test_format_user_left_message_contains_user_and_hashtag() -> None:
    user = ChatUser(id=77, mention_html="<a href='tg://user?id=77'>User</a>", username="tester")
    moment = datetime(2026, 4, 15, 12, 30, tzinfo=ZoneInfo("Europe/Moscow"))

    rendered_message = format_user_left_message(user, moment)

    assert "Пользователь" in rendered_message
    assert "#id77" in rendered_message
    assert "@tester" in rendered_message


def test_format_user_restricted_message_uses_change_set() -> None:
    old_member = SimpleNamespace(
        status=ChatMemberStatus.ADMINISTRATOR,
        can_send_messages=None,
    )
    new_member = SimpleNamespace(
        status=ChatMemberStatus.RESTRICTED,
        can_send_messages=False,
    )
    user = ChatUser(id=9, mention_html="<b>Admin</b>", username=None)

    change_set = describe_restricted_rights_changes(old_member, new_member)

    assert change_set is not None
    rendered_message = format_user_restricted_message(
        user=user,
        change_set=change_set,
        moment=datetime(2026, 4, 15, 12, 30, tzinfo=ZoneInfo("Europe/Moscow")),
    )
    assert "Сняли права администратора" in rendered_message
    assert "#id9" in rendered_message

