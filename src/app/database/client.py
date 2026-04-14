from app.database.custom_command_db import CustomCommandDB
from app.database.greetings_db import GreetingsDB


class ClientDB:
    db_path: str | None = "bot.db"

    if db_path is None:
        raise ValueError("`db_path` cannot be nullable")

    if not isinstance(db_path, str):
        raise TypeError("`db_path` must be a string")

    custom_command = CustomCommandDB(db_path)
    greetings = GreetingsDB(db_path)
