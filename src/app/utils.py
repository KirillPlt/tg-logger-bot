
def shifted_id(native_chat_id: int) -> int:
    short_id = str(native_chat_id).replace("-100", "")
    shift = int(-1 * pow(10, len(short_id) + 2))
    return shift - native_chat_id


def text_size_bytes(text: str, encoding: str = "utf-8") -> int:
    return len(text.encode(encoding))
