from app.presentation.parsers import LIST_COMMANDS_REQUEST, parse_create_command, parse_delete_command


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

