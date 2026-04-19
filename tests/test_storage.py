import json
import threading
import time
from pathlib import Path

from backend.schemas import MessageCreate
from backend.storage import (
    append_message,
    init_storage,
    read_messages,
    read_participants,
    read_session,
    read_settings,
    storage_path,
)


def test_init_storage_creates_directory(storage_dir: Path) -> None:
    init_storage(storage_dir)
    assert (storage_dir / ".ai-boardroom").is_dir()


def test_init_storage_creates_all_files(storage_dir: Path) -> None:
    init_storage(storage_dir)
    root = storage_dir / ".ai-boardroom"
    assert (root / "session.json").is_file()
    assert (root / "participants.json").is_file()
    assert (root / "transcript.jsonl").is_file()
    assert (root / "settings.json").is_file()


def test_init_storage_is_idempotent(storage_dir: Path) -> None:
    init_storage(storage_dir)
    transcript = storage_dir / ".ai-boardroom" / "transcript.jsonl"
    transcript.write_text('{"id":"msg-001"}\n', encoding="utf-8")
    init_storage(storage_dir)
    assert transcript.read_text(encoding="utf-8") == '{"id":"msg-001"}\n'


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
    transcript = initialized_storage / ".ai-boardroom" / "transcript.jsonl"
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
    transcript = initialized_storage / ".ai-boardroom" / "transcript.jsonl"
    lines = transcript.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["sender"] == "User"
    assert parsed["id"] == "msg-001"


def test_append_message_updates_session_updated_at(initialized_storage: Path) -> None:
    before = read_session(initialized_storage).updatedAt
    time.sleep(1.1)
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
    transcript = initialized_storage / ".ai-boardroom" / "transcript.jsonl"
    lines = [line for line in transcript.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 20
