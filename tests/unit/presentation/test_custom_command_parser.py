from app.presentation.parsers import (
    CREATE_GREETING_PREFIX,
    CREATE_NOTE_PREFIX,
    LIST_COMMANDS_REQUEST,
    parse_create_command,
    parse_create_greeting,
    parse_create_note,
    parse_delete_command,
)


def test_parse_create_command_extracts_html_payload() -> None:
    parsed_command = parse_create_command(
        "+команда привет\n<b>Мир</b>",
        "+команда привет\n<b>Мир</b>",
    )

    assert parsed_command is not None
    assert parsed_command.name == "привет"
    assert parsed_command.response_html == "<b>Мир</b>"


def test_parse_delete_command_returns_command_name() -> None:
    assert parse_delete_command("-команда привет") == "привет"


def test_list_commands_request_is_stable() -> None:
    assert LIST_COMMANDS_REQUEST == "?команды"


def test_parse_create_greeting_extracts_html_payload() -> None:
    parsed_greeting = parse_create_greeting(
        f"{CREATE_GREETING_PREFIX}\n<b>Привет</b>",
        f"{CREATE_GREETING_PREFIX}\n<b>Привет</b>",
    )

    assert parsed_greeting is not None
    assert parsed_greeting.response_html == "<b>Привет</b>"


def test_parse_create_note_extracts_name_and_html_payload() -> None:
    parsed_note = parse_create_note(
        f"{CREATE_NOTE_PREFIX} наказание\n<b>Текст</b>",
        f"{CREATE_NOTE_PREFIX} наказание\n<b>Текст</b>",
    )

    assert parsed_note is not None
    assert parsed_note.name == "наказание"
    assert parsed_note.response_html == "<b>Текст</b>"
