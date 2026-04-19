# Phase 2 — Storage Layer

**Prerequisites:** [Phase 1 — Foundation](phase-1-foundation.md) complete. Schemas and ID generator must import cleanly.

**Phase Goal:** Implement the project-local `.ai-boardroom/` directory layer — initialization, reads for session/participants/messages/settings, and the append path that writes new messages to `transcript.jsonl` and bumps `session.updatedAt`.

**Completion Criteria:**
- `pytest tests/test_storage.py -v` shows 15 PASSED (includes concurrency test firing 20 parallel appends)
- A fresh test run creates and tears down `.ai-boardroom/` under `tmp_path` without errors
- `session.json` and `transcript.jsonl` round-trip a message through `append_message` + `read_messages`
- IDs are allocated from `session.json::nextMessageId` under a `threading.Lock`; duplicate IDs under concurrency are impossible within a single Uvicorn worker

**Next Phase:** [Phase 3 — HTTP API](phase-3-api.md)

---

## Task 4: Storage Layer — Initialization

**Files:**
- Create: `backend/storage.py`
- Create: `tests/conftest.py`
- Test: `tests/test_storage.py` (initialization cases)

- [ ] **Step 1: Write the conftest fixture**

Create `tests/conftest.py`:

```python
import pytest
from pathlib import Path


@pytest.fixture
def storage_dir(tmp_path: Path) -> Path:
    """Temporary project folder containing no .ai-boardroom yet."""
    return tmp_path


@pytest.fixture
def initialized_storage(storage_dir: Path) -> Path:
    """Temporary project folder with .ai-boardroom/ already initialized."""
    from backend.storage import init_storage
    init_storage(storage_dir)
    return storage_dir
```

- [ ] **Step 2: Write failing init tests**

Create `tests/test_storage.py`:

```python
from pathlib import Path
from backend.storage import init_storage, storage_path


def test_init_storage_creates_directory(storage_dir: Path):
    init_storage(storage_dir)
    assert (storage_dir / ".ai-boardroom").is_dir()


def test_init_storage_creates_all_files(storage_dir: Path):
    init_storage(storage_dir)
    root = storage_dir / ".ai-boardroom"
    assert (root / "session.json").is_file()
    assert (root / "participants.json").is_file()
    assert (root / "transcript.jsonl").is_file()
    assert (root / "settings.json").is_file()


def test_init_storage_is_idempotent(storage_dir: Path):
    init_storage(storage_dir)
    transcript = storage_dir / ".ai-boardroom" / "transcript.jsonl"
    transcript.write_text('{"id":"msg-001"}\n', encoding="utf-8")
    init_storage(storage_dir)
    assert transcript.read_text(encoding="utf-8") == '{"id":"msg-001"}\n'


def test_storage_path_returns_ai_boardroom_subdir(storage_dir: Path):
    assert storage_path(storage_dir) == storage_dir / ".ai-boardroom"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_storage.py -v`
Expected: `ModuleNotFoundError: No module named 'backend.storage'`.

- [ ] **Step 4: Implement init_storage**

Create `backend/storage.py`:

```python
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from backend.schemas import Message, Participant, Session

STORAGE_DIRNAME = ".ai-boardroom"

DEFAULT_PARTICIPANTS: List[dict] = [
    {"name": "User", "type": "human", "role": "facilitator"},
    {"name": "Codex", "type": "agent", "role": "implementation, feasibility, architecture, execution details"},
    {"name": "Claude", "type": "agent", "role": "reasoning, critique, writing clarity, tradeoffs"},
    {"name": "Gemini", "type": "agent", "role": "ideation, alternatives, synthesis, reframing"},
]

DEFAULT_SETTINGS: dict = {
    "pollIntervalMs": 1500,
    "roomName": "main",
}


def storage_path(project_root: Path) -> Path:
    return project_root / STORAGE_DIRNAME


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def init_storage(project_root: Path) -> None:
    root = storage_path(project_root)
    root.mkdir(parents=True, exist_ok=True)

    session_file = root / "session.json"
    if not session_file.exists():
        session = Session(
            id=f"sess-{uuid.uuid4().hex[:8]}",
            projectPath=str(project_root.resolve()),
            createdAt=_now(),
            updatedAt=_now(),
            roomName="main",
        )
        session_file.write_text(session.model_dump_json(indent=2), encoding="utf-8")

    participants_file = root / "participants.json"
    if not participants_file.exists():
        participants_file.write_text(
            json.dumps(DEFAULT_PARTICIPANTS, indent=2), encoding="utf-8"
        )

    transcript_file = root / "transcript.jsonl"
    if not transcript_file.exists():
        transcript_file.touch()

    settings_file = root / "settings.json"
    if not settings_file.exists():
        settings_file.write_text(json.dumps(DEFAULT_SETTINGS, indent=2), encoding="utf-8")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_storage.py -v`
Expected: 4 PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/storage.py tests/conftest.py tests/test_storage.py
git commit -m "feat: add storage init for .ai-boardroom directory"
```

---

## Task 5: Storage Layer — Read Helpers

**Files:**
- Modify: `backend/storage.py` (add read functions)
- Modify: `tests/test_storage.py` (add read tests)

- [ ] **Step 1: Write failing read tests**

Append to `tests/test_storage.py`:

```python
from backend.storage import (
    read_session,
    read_participants,
    read_messages,
    read_settings,
)


def test_read_session_returns_session_model(initialized_storage):
    session = read_session(initialized_storage)
    assert session.roomName == "main"
    assert session.id.startswith("sess-")


def test_read_participants_returns_four_defaults(initialized_storage):
    parts = read_participants(initialized_storage)
    names = [p.name for p in parts]
    assert names == ["User", "Codex", "Claude", "Gemini"]


def test_read_messages_empty_on_fresh_init(initialized_storage):
    assert read_messages(initialized_storage) == []


def test_read_messages_returns_stored_messages(initialized_storage):
    transcript = initialized_storage / ".ai-boardroom" / "transcript.jsonl"
    lines = [
        '{"id":"msg-001","roomId":"main","sender":"User","senderType":"human","text":"hi","mentions":[],"replyTo":null,"timestamp":"2026-04-19T14:00:00-05:00"}',
        '{"id":"msg-002","roomId":"main","sender":"Codex","senderType":"agent","text":"hello","mentions":["user"],"replyTo":"msg-001","timestamp":"2026-04-19T14:00:01-05:00"}',
    ]
    transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")
    msgs = read_messages(initialized_storage)
    assert len(msgs) == 2
    assert msgs[0].id == "msg-001"
    assert msgs[1].replyTo == "msg-001"


def test_read_settings_returns_defaults(initialized_storage):
    s = read_settings(initialized_storage)
    assert s["roomName"] == "main"
    assert s["pollIntervalMs"] == 1500
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_storage.py -v -k "read_"`
Expected: `ImportError: cannot import name 'read_session' ...`.

- [ ] **Step 3: Implement read helpers**

Append to `backend/storage.py`:

```python
def read_session(project_root: Path) -> Session:
    raw = (storage_path(project_root) / "session.json").read_text(encoding="utf-8")
    return Session.model_validate_json(raw)


def read_participants(project_root: Path) -> List[Participant]:
    raw = (storage_path(project_root) / "participants.json").read_text(encoding="utf-8")
    data = json.loads(raw)
    return [Participant.model_validate(p) for p in data]


def read_messages(project_root: Path) -> List[Message]:
    transcript = storage_path(project_root) / "transcript.jsonl"
    messages: List[Message] = []
    for line in transcript.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        messages.append(Message.model_validate_json(line))
    return messages


def read_settings(project_root: Path) -> dict:
    raw = (storage_path(project_root) / "settings.json").read_text(encoding="utf-8")
    return json.loads(raw)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_storage.py -v`
Expected: 9 PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/storage.py tests/test_storage.py
git commit -m "feat: add read helpers for session, participants, messages, settings"
```

---

## Task 6: Storage Layer — Append Message

**Files:**
- Modify: `backend/storage.py` (add append_message, update_session_timestamp)
- Modify: `tests/test_storage.py` (add append tests)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_storage.py`:

```python
from backend.schemas import MessageCreate
from backend.storage import append_message


def test_append_message_assigns_id_and_timestamp(initialized_storage):
    payload = MessageCreate(sender="User", senderType="human", text="hello")
    stored = append_message(initialized_storage, payload, room_id="main")
    assert stored.id == "msg-001"
    assert stored.roomId == "main"
    assert stored.timestamp  # non-empty ISO string


def test_append_message_increments_ids(initialized_storage):
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


def test_append_message_writes_jsonl_line(initialized_storage):
    append_message(
        initialized_storage,
        MessageCreate(sender="User", senderType="human", text="hi"),
        room_id="main",
    )
    transcript = initialized_storage / ".ai-boardroom" / "transcript.jsonl"
    lines = transcript.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    import json as _json
    parsed = _json.loads(lines[0])
    assert parsed["sender"] == "User"
    assert parsed["id"] == "msg-001"


def test_append_message_updates_session_updated_at(initialized_storage):
    before = read_session(initialized_storage).updatedAt
    import time
    time.sleep(1.1)  # ensure ISO-second granularity ticks
    append_message(
        initialized_storage,
        MessageCreate(sender="User", senderType="human", text="hi"),
        room_id="main",
    )
    after = read_session(initialized_storage).updatedAt
    assert after > before


def test_append_message_advances_session_counter(initialized_storage):
    append_message(
        initialized_storage,
        MessageCreate(sender="User", senderType="human", text="one"),
        room_id="main",
    )
    assert read_session(initialized_storage).nextMessageId == 2


def test_append_message_assigns_unique_ids_under_concurrency(initialized_storage):
    """Multiple agents posting concurrently must not collide on IDs.
    Reason: product is designed for 3+ agents posting into one room."""
    import threading
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
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 20
    assert len(set(results)) == 20, f"duplicate IDs: {results}"
    # Transcript should also contain 20 distinct lines
    transcript = initialized_storage / ".ai-boardroom" / "transcript.jsonl"
    lines = [ln for ln in transcript.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 20
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_storage.py::test_append_message_assigns_id_and_timestamp -v`
Expected: `ImportError: cannot import name 'append_message' ...`.

- [ ] **Step 3: Implement append_message (with lock + session counter)**

Append to `backend/storage.py`:

```python
import os
import threading

from backend.ids import format_message_id

_append_lock = threading.Lock()


def _write_session_atomic(project_root: Path, session: Session) -> None:
    """Write session.json via write-to-temp + os.replace so readers never see
    a half-written file. Required because we update the counter and timestamp
    on every append."""
    target = storage_path(project_root) / "session.json"
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(session.model_dump_json(indent=2), encoding="utf-8")
    os.replace(tmp, target)


def append_message(
    project_root: Path, payload: MessageCreate, room_id: str = "main"
) -> Message:
    # Lock the full read-counter / write-transcript / write-session sequence.
    # Without this, two concurrent agent posts can both read nextMessageId=N,
    # both format "msg-N", and both append — producing duplicate IDs in a
    # multi-agent workflow.
    with _append_lock:
        session = read_session(project_root)
        message = Message(
            id=format_message_id(session.nextMessageId),
            roomId=room_id,
            sender=payload.sender,
            senderType=payload.senderType,
            text=payload.text,
            mentions=payload.mentions,
            replyTo=payload.replyTo,
            timestamp=_now(),
        )
        transcript = storage_path(project_root) / "transcript.jsonl"
        with transcript.open("a", encoding="utf-8") as fh:
            fh.write(message.model_dump_json() + "\n")
        session.nextMessageId += 1
        session.updatedAt = _now()
        _write_session_atomic(project_root, session)
        return message
```

> **Concurrency scope:** `threading.Lock` serializes appends within a single
> Uvicorn worker. MVP runs single-worker (the default). Multi-worker
> deployments would need a cross-process lock (e.g. `filelock`) — explicitly
> out of MVP scope per ADR 0001.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_storage.py -v`
Expected: 15 PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/storage.py tests/test_storage.py
git commit -m "feat: append_message writes JSONL and bumps session timestamp"
```
