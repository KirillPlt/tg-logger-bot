import re
from dataclasses import dataclass
from re import Match


CREATE_COMMAND_PREFIX = "+команда"
CREATE_GREETING_PREFIX = "+приветствие"
CREATE_NOTE_PREFIX = "+заметка"
DELETE_COMMAND_PREFIX = "-команда"
LIST_COMMANDS_REQUEST = "?команды"


CREATE_COMMAND_PATTERN = re.compile(
    rf"^{re.escape(CREATE_COMMAND_PREFIX)}\s+([^\n]+?)\s*\n([\s\S]+)$"
)
CREATE_NOTE_PATTERN = re.compile(
    rf"^{re.escape(CREATE_NOTE_PREFIX)}\s+([^\n]+?)\s*\n([\s\S]+)$"
)
CREATE_GREETING_PATTERN = re.compile(
    rf"^{re.escape(CREATE_GREETING_PREFIX)}\s*\n([\s\S]+)$"
)
DELETE_COMMAND_PATTERN = re.compile(
    rf"^{re.escape(DELETE_COMMAND_PREFIX)}\s+([^\n]+?)\s*$"
)


@dataclass(frozen=True, slots=True)
class ParsedCreateCommand:
    name: str
    response_html: str


@dataclass(frozen=True, slots=True)
class ParsedCreateGreeting:
    response_html: str


@dataclass(frozen=True, slots=True)
class ParsedCreateNote:
    name: str
    response_html: str


def parse_create_command(
    plain_text: str | None,
    html_text: str | None,
) -> ParsedCreateCommand | None:
    parsed_payload = _parse_named_multiline_payload(
        plain_text,
        html_text,
        CREATE_COMMAND_PATTERN,
    )
    if parsed_payload is None:
        return None

    name, response_html = parsed_payload
    return ParsedCreateCommand(name=name, response_html=response_html)


def parse_create_greeting(
    plain_text: str | None,
    html_text: str | None,
) -> ParsedCreateGreeting | None:
    parsed_payload = _parse_greeting_payload(
        plain_text,
        html_text,
    )
    if parsed_payload is None:
        return None

    return ParsedCreateGreeting(response_html=parsed_payload)


def parse_create_note(
    plain_text: str | None,
    html_text: str | None,
) -> ParsedCreateNote | None:
    parsed_payload = _parse_named_multiline_payload(
        plain_text,
        html_text,
        CREATE_NOTE_PATTERN,
    )
    if parsed_payload is None:
        return None

    name, response_html = parsed_payload
    return ParsedCreateNote(name=name, response_html=response_html)


def parse_delete_command(plain_text: str | None) -> str | None:
    if plain_text is None:
        return None

    match: Match[str] | None = DELETE_COMMAND_PATTERN.match(plain_text)
    if match is None:
        return None

    command_name = match.group(1).strip()
    return command_name or None


def _parse_named_multiline_payload(
    plain_text: str | None,
    html_text: str | None,
    pattern: re.Pattern[str],
) -> tuple[str, str] | None:
    if plain_text is None or html_text is None:
        return None

    match: Match[str] | None = pattern.match(plain_text)
    if match is None:
        return None

    name = match.group(1).strip()
    html_parts = html_text.split("\n", maxsplit=1)
    if len(html_parts) < 2:
        return None

    response_html = html_parts[1].strip()
    if not name or not response_html:
        return None

    return name, response_html


def _parse_greeting_payload(
    plain_text: str | None,
    html_text: str | None,
) -> str | None:
    if plain_text is None or html_text is None:
        return None

    match: Match[str] | None = CREATE_GREETING_PATTERN.match(plain_text)
    if match is None:
        return None

    html_parts = html_text.split("\n", maxsplit=1)
    if len(html_parts) < 2:
        return None

    response_html = html_parts[1].strip()
    return response_html or None
