import re
from dataclasses import dataclass
from re import Match


CREATE_COMMAND_PREFIX = "+команда"
DELETE_COMMAND_PREFIX = "-команда"
LIST_COMMANDS_REQUEST = "?команды"


CREATE_COMMAND_PATTERN = re.compile(
    rf"^{re.escape(CREATE_COMMAND_PREFIX)}\s+([^\n]+?)\s*\n([\s\S]+)$"
)
DELETE_COMMAND_PATTERN = re.compile(
    rf"^{re.escape(DELETE_COMMAND_PREFIX)}\s+([^\n]+?)\s*$"
)


@dataclass(frozen=True, slots=True)
class ParsedCreateCommand:
    name: str
    response_html: str


def parse_create_command(
    plain_text: str | None,
    html_text: str | None,
) -> ParsedCreateCommand | None:
    if plain_text is None or html_text is None:
        return None

    match: Match[str] | None = CREATE_COMMAND_PATTERN.match(plain_text)
    if match is None:
        return None

    name = match.group(1).strip()
    html_parts = html_text.split("\n", maxsplit=1)

    if len(html_parts) < 2:
        return None

    response_html = html_parts[1].strip()
    if not name or not response_html:
        return None

    return ParsedCreateCommand(name=name, response_html=response_html)


def parse_delete_command(plain_text: str | None) -> str | None:
    if plain_text is None:
        return None

    match: Match[str] | None = DELETE_COMMAND_PATTERN.match(plain_text)
    if match is None:
        return None

    command_name = match.group(1).strip()
    return command_name or None
