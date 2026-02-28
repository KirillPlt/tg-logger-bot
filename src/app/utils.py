
def shifted_id(native_chat_id: int) -> int:
    short_id = str(native_chat_id).replace("-100", "")
    shift = int(-1 * pow(10, len(short_id) + 2))
    return shift - native_chat_id


def text_size_bytes(text: str, encoding: str = "utf-8") -> int:
    return len(text.encode(encoding))


def user_rules_analysis(old: list[bool], new: list[bool]) -> str:
    rules = [
        "Может отправлять аудио",
        "Может отправлять документы",
        "Может отправлять сообщения",
        "Может отправлять стикеры, GIF и т.д.",
        "Может отправлять фото",
        "Может отправлять опросы",
        "Может отправлять видео-кружочки",
        "Может отправлять видео",
        "Может отправлять ГС",
    ]

    result: list[str] = []

    for i, (old_rule, new_rule) in enumerate(zip(old, new)):
        if old_rule == new_rule:
            continue

        if new_rule:
            result.append(rules[i])
        else:
            result.append(f"Не {rules[i][0].lower()}{rules[i][1:]}")

    return "\n".join(result)

