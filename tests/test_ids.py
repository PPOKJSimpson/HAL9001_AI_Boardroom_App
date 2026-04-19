from backend.ids import format_message_id, next_message_id_from_count


def test_format_message_id_pads_to_three_digits():
    assert format_message_id(1) == "msg-001"
    assert format_message_id(42) == "msg-042"
    assert format_message_id(104) == "msg-104"


def test_format_message_id_allows_four_digits():
    assert format_message_id(1000) == "msg-1000"


def test_next_message_id_from_count_increments():
    assert next_message_id_from_count(0) == "msg-001"
    assert next_message_id_from_count(3) == "msg-004"
