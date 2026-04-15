from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BotRuntimeSettings:
    reaction_logs_enabled: bool = True
