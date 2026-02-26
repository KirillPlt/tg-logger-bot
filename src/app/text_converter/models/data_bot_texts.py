from dataclasses import dataclass

type Text = str

@dataclass
class BotTexts:
    text: list[Text] | None