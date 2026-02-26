import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv

from app.text_converter.models.data_bot_texts import BotTexts, Text


class ITextConnector(ABC):
    @abstractmethod
    def parse(self, path: str | None = None) -> BotTexts: ...


class Converter(ITextConnector):
    def parse(self, path: str | None = None) -> BotTexts:
        load_dotenv(dotenv_path='.env')

        left_user_event: Text = os.getenv("left_user_event")
        admin_kick_user_event: Text = os.getenv("admin_kick_user_event")
        join_user_event: Text = os.getenv("join_user_event")
        edit_message_event: Text = os.getenv("edit_message_event")
        restricted_user_event: Text = os.getenv("restricted_user_event")

        bot_texts: BotTexts | None = BotTexts.text

        bot_texts.text.append(left_user_event)
        bot_texts.text.append(admin_kick_user_event)
        bot_texts.text.append(join_user_event)
        bot_texts.text.append(edit_message_event)
        bot_texts.text.append(restricted_user_event)

        return bot_texts

