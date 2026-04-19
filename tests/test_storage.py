import json
import threading
from pathlib import Path

from backend.schemas import MessageCreate
from backend.storage import (
    activate_session,
    append_message,
    create_session,
    current_session_pointer,
    ensure_current_session,
    get_current_session_id,
    init_storage,
    list_sessions,
    read_messages,
    read_participants,
    read_session,
    read_settings,
    set_current_session_id,
    storage_path,
    update_session_title,
)


def test_init_storage_creates_directory(storage_dir: Path) -> None:
    init_storage(storage_dir)
    assert (storage_dir / ".ai-boardroom").is_dir()


def test_init_storage_creates_all_files(storage_dir: Path) -> None:
    init_storage(storage_dir)
    root = storage_dir / ".ai-boardroom"
    assert (root / "participants.json").is_file()
    assert (root / "settings.json").is_file()
    assert (root / "sessions").is_dir()


def test_init_storage_is_idempotent(storage_dir: Path) -> None:
    init_storage(storage_dir)
    participants = storage_dir / ".ai-boardroom" / "participants.json"
    participants.write_text('[{"name":"User","type":"human"}]\n', encoding="utf-8")
    init_storage(storage_dir)
    assert participants.read_text(encoding="utf-8") == '[{"name":"User","type":"human"}]\n'


def test_storage_path_returns_ai_boardroom_subdir(storage_dir: Path) -> None:
    assert storage_path(storage_dir) == storage_dir / ".ai-boardroom"


def test_read_session_returns_session_model(initialized_storage: Path) -> None:
    session = read_session(initialized_storage)
    assert session.roomName == "main"
    assert session.id.startswith("sess-")


def test_read_participants_returns_four_defaults(initialized_storage: Path) -> None:
    participants = read_participants(initialized_storage)
    names = [participant.name for participant in participants]
    assert names == ["User", "Codex", "Claude", "Gemini"]


def test_read_messages_empty_on_fresh_init(initialized_storage: Path) -> None:
    assert read_messages(initialized_storage) == []


def test_read_messages_returns_stored_messages(initialized_storage: Path) -> None:
    transcript = initialized_storage / ".ai-boardroom" / "sessions" / read_session(initialized_storage).id / "transcript.jsonl"
    lines = [
        '{"id":"msg-001","roomId":"main","sender":"User","senderType":"human","text":"hi","mentions":[],"replyTo":null,"timestamp":"2026-04-19T14:00:00-05:00"}',
        '{"id":"msg-002","roomId":"main","sender":"Codex","senderType":"agent","text":"hello","mentions":["user"],"replyTo":"msg-001","timestamp":"2026-04-19T14:00:01-05:00"}',
    ]
    transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")
    messages = read_messages(initialized_storage)
    assert len(messages) == 2
    assert messages[0].id == "msg-001"
    assert messages[1].replyTo == "msg-001"


def test_read_settings_returns_defaults(initialized_storage: Path) -> None:
    settings = read_settings(initialized_storage)
    assert settings["roomName"] == "main"
    assert settings["pollIntervalMs"] == 1500


def test_append_message_assigns_id_and_timestamp(initialized_storage: Path) -> None:
    payload = MessageCreate(sender="User", senderType="human", text="hello")
    stored = append_message(initialized_storage, payload, room_id="main")
    assert stored.id == "msg-001"
    assert stored.roomId == "main"
    assert stored.timestamp


def test_append_message_increments_ids(initialized_storage: Path) -> None:
    first = append_message(
        initialized_storage,
        MessageCreate(sender="User", senderType="human", text="one"),
        room_id="main",
    )
    second = append_message(
        initialized_storage,
        MessageCreate(sender="Codex", senderType="agent", text="two"),
        room_id="main",
    )
    assert first.id == "msg-001"
    assert second.id == "msg-002"


def test_append_message_writes_jsonl_line(initialized_storage: Path) -> None:
    append_message(
        initialized_storage,
        MessageCreate(sender="User", senderType="human", text="hi"),
        room_id="main",
    )
    transcript = initialized_storage / ".ai-boardroom" / "sessions" / read_session(initialized_storage).id / "transcript.jsonl"
    lines = transcript.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["sender"] == "User"
    assert parsed["id"] == "msg-001"


def test_append_message_updates_session_updated_at(initialized_storage: Path) -> None:
    before = read_session(initialized_storage).updatedAt
    append_message(
        initialized_storage,
        MessageCreate(sender="User", senderType="human", text="hi"),
        room_id="main",
    )
    after = read_session(initialized_storage).updatedAt
    assert after > before


def test_append_message_advances_session_counter(initialized_storage: Path) -> None:
    append_message(
        initialized_storage,
        MessageCreate(sender="User", senderType="human", text="one"),
        room_id="main",
    )
    assert read_session(initialized_storage).nextMessageId == 2


def test_append_message_assigns_unique_ids_under_concurrency(
    initialized_storage: Path,
) -> None:
    results: list[str] = []
    results_lock = threading.Lock()

    def poster(n: int) -> None:
        stored = append_message(
            initialized_storage,
            MessageCreate(sender="Codex", senderType="agent", text=f"msg {n}"),
            room_id="main",
        )
        with results_lock:
            results.append(stored.id)

    threads = [threading.Thread(target=poster, args=(i,)) for i in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 20
    assert len(set(results)) == 20, f"duplicate IDs: {results}"
    transcript = initialized_storage / ".ai-boardroom" / "sessions" / read_session(initialized_storage).id / "transcript.jsonl"
    lines = [line for line in transcript.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 20


def test_init_storage_fresh_root_creates_sessions_dir_but_no_session_files(storage_dir: Path) -> None:
    init_storage(storage_dir)
    root = storage_dir / ".ai-boardroom"
    assert (root / "sessions").is_dir()
    assert list((root / "sessions").iterdir()) == []
    assert not current_session_pointer(storage_dir).exists()


def test_init_storage_migrates_legacy_layout(legacy_storage: Path) -> None:
    init_storage(legacy_storage)
    root = legacy_storage / ".ai-boardroom"
    migrated_dir = root / "sessions" / "sess-legacy01"
    assert migrated_dir.is_dir()
    assert (migrated_dir / "session.json").is_file()
    assert (migrated_dir / "transcript.jsonl").is_file()
    assert not (root / "session.json").exists()
    assert not (root / "transcript.jsonl").exists()
    assert get_current_session_id(legacy_storage) == "sess-legacy01"


def test_init_storage_already_migrated_is_stable(legacy_storage: Path) -> None:
    init_storage(legacy_storage)
    migrated_dir = legacy_storage / ".ai-boardroom" / "sessions" / "sess-legacy01"
    before = (migrated_dir / "session.json").read_text(encoding="utf-8")
    init_storage(legacy_storage)
    after = (migrated_dir / "session.json").read_text(encoding="utf-8")
    assert before == after


def test_create_session_writes_session_folder(storage_dir: Path) -> None:
    init_storage(storage_dir)
    session = create_session(storage_dir, title="Planning")
    assert (storage_dir / ".ai-boardroom" / "sessions" / session.id / "session.json").is_file()
    assert session.title == "Planning"


def test_list_sessions_returns_newest_first(storage_dir: Path) -> None:
    init_storage(storage_dir)
    first = create_session(storage_dir, title="One")
    second = create_session(storage_dir, title="Two")
    sessions = list_sessions(storage_dir)
    assert [session.id for session in sessions] == [second.id, first.id]
    assert sessions[0].messageCount == 0


def test_ensure_current_session_creates_pointer_when_missing(storage_dir: Path) -> None:
    init_storage(storage_dir)
    session = ensure_current_session(storage_dir)
    assert get_current_session_id(storage_dir) == session.id


def test_ensure_current_session_returns_existing_pointer(initialized_storage: Path) -> None:
    session = read_session(initialized_storage)
    ensured = ensure_current_session(initialized_storage)
    assert ensured.id == session.id


def test_ensure_current_session_replaces_stale_pointer(storage_dir: Path) -> None:
    init_storage(storage_dir)
    set_current_session_id(storage_dir, "sess-missing")
    ensured = ensure_current_session(storage_dir)
    assert ensured.id != "sess-missing"
    assert get_current_session_id(storage_dir) == ensured.id


def test_activate_session_switches_current_pointer(storage_dir: Path) -> None:
    init_storage(storage_dir)
    first = create_session(storage_dir)
    second = create_session(storage_dir)
    set_current_session_id(storage_dir, first.id)
    activate_session(storage_dir, second.id)
    assert read_session(storage_dir).id == second.id


def test_activate_session_unknown_raises_key_error(storage_dir: Path) -> None:
    init_storage(storage_dir)
    try:
        activate_session(storage_dir, "sess-missing")
    except KeyError as exc:
        assert exc.args == ("sess-missing",)
    else:
        raise AssertionError("Expected KeyError for missing session")


def test_update_session_title_round_trips(storage_dir: Path) -> None:
    init_storage(storage_dir)
    session = create_session(storage_dir)
    updated = update_session_title(storage_dir, session.id, "API contract review")
    assert updated.title == "API contract review"
    assert read_session(storage_dir, session_id=session.id).title == "API contract review"


def test_append_message_only_touches_current_session(storage_dir: Path) -> None:
    init_storage(storage_dir)
    first = create_session(storage_dir)
    second = create_session(storage_dir)
    set_current_session_id(storage_dir, first.id)
    append_message(storage_dir, MessageCreate(sender="User", senderType="human", text="one"))
    activate_session(storage_dir, second.id)
    append_message(storage_dir, MessageCreate(sender="User", senderType="human", text="two"))
    assert [message.text for message in read_messages(storage_dir, session_id=first.id)] == ["one"]
    assert [message.text for message in read_messages(storage_dir, session_id=second.id)] == ["two"]
