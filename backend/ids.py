def format_message_id(n: int) -> str:
    return f"msg-{n:03d}"


def next_message_id_from_count(existing_count: int) -> str:
    return format_message_id(existing_count + 1)
