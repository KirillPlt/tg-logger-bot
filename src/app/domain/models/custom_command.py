from dataclasses import dataclass


MAX_CUSTOM_COMMAND_NAME_LENGTH = 64


@dataclass(frozen=True, slots=True)
class CustomCommand:
    normalized_name: str
    display_name: str
    response_html: str


def sanitize_command_name(name: str) -> str:
    sanitized_name = " ".join(name.split()).strip()

    if not sanitized_name:
        raise ValueError("Имя команды не может быть пустым.")

    if len(sanitized_name) > MAX_CUSTOM_COMMAND_NAME_LENGTH:
        raise ValueError(
            f"Имя команды не должно превышать {MAX_CUSTOM_COMMAND_NAME_LENGTH} символа(ов)."
        )

    return sanitized_name


def normalize_command_name(name: str) -> str:
    return sanitize_command_name(name).casefold()
