from dataclasses import dataclass
from typing import Any

from aiogram.enums import ChatMemberStatus


ADMIN_RIGHTS_TITLES = {
    "can_manage_chat": "Управление чатом",
    "can_change_info": "Изменение информации",
    "can_delete_messages": "Удаление сообщений",
    "can_restrict_members": "Мут / бан",
    "can_invite_users": "Приглашение пользователей",
    "can_pin_messages": "Закреп сообщений",
    "can_manage_topics": "Управление темами",
    "can_manage_video_chats": "Видео-чаты",
    "can_promote_members": "Назначение админов",
    "is_anonymous": "Анонимный админ",
}


RESTRICTED_RIGHTS_TITLES = {
    "can_send_messages": "Отправлять сообщения",
    "can_send_photos": "Отправлять фото",
    "can_send_videos": "Отправлять видео",
    "can_send_video_notes": "Видео-кружочки",
    "can_send_voice_notes": "Голосовые",
    "can_send_audios": "Аудио",
    "can_send_documents": "Документы",
    "can_send_polls": "Опросы",
    "can_send_other_messages": "Стикеры / GIF",
    "can_invite_users": "Приглашение пользователей",
}

UNRESTRICTED_MEMBER_STATUSES = frozenset(
    {
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.MEMBER,
    }
)
NO_ACCESS_MEMBER_STATUSES = frozenset({ChatMemberStatus.LEFT, ChatMemberStatus.KICKED})


@dataclass(frozen=True, slots=True)
class RestrictedRightsChangeSet:
    lines: tuple[str, ...]
    includes_admin_demotion: bool


def format_admin_rights(member: Any) -> str:
    lines = []

    for index, (attribute_name, title) in enumerate(ADMIN_RIGHTS_TITLES.items(), start=1):
        value = bool(getattr(member, attribute_name, False))
        lines.append(f"{index}. {title}: {'✅' if value else '❌'}")

    return "\n".join(lines)


def describe_restricted_rights_changes(
    old_member: Any,
    new_member: Any,
) -> RestrictedRightsChangeSet | None:
    includes_admin_demotion = (
        getattr(old_member, "status", None) == ChatMemberStatus.ADMINISTRATOR
        and getattr(new_member, "status", None) != ChatMemberStatus.ADMINISTRATOR
    )
    lines: list[str] = []

    for attribute_name, title in RESTRICTED_RIGHTS_TITLES.items():
        old_value = _resolve_restricted_right_value(old_member, attribute_name)
        new_value = _resolve_restricted_right_value(new_member, attribute_name)

        if old_value is None and new_value is None:
            continue

        if old_value == new_value:
            continue

        if old_value is None:
            lines.append(f"{title}: {_format_restricted_right_state(new_value)}")
            continue

        if new_value is None:
            lines.append(f"{title}: {_format_restricted_right_state(old_value)}")
            continue

        lines.append(
            f"{title}: {_format_restricted_right_state(old_value)} → "
            f"{_format_restricted_right_state(new_value)}"
        )

    if not lines and not includes_admin_demotion:
        return None

    return RestrictedRightsChangeSet(
        lines=tuple(lines),
        includes_admin_demotion=includes_admin_demotion,
    )


def _resolve_restricted_right_value(member: Any, attribute_name: str) -> bool | None:
    value = getattr(member, attribute_name, None)
    if value is not None:
        return bool(value)

    status = getattr(member, "status", None)
    if status == ChatMemberStatus.RESTRICTED:
        return None

    if status in UNRESTRICTED_MEMBER_STATUSES:
        return True

    if status in NO_ACCESS_MEMBER_STATUSES:
        return False

    return None


def _format_restricted_right_state(value: bool | None) -> str:
    return "✅" if value else "❌"
