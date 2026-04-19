import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.ids import format_message_id
from backend.schemas import Message, MessageCreate, Participant, Session, SessionSummary

STORAGE_DIRNAME = ".ai-boardroom"

DEFAULT_PARTICIPANTS: list[dict[str, Any]] = [
    {"name": "User", "type": "human", "role": "facilitator"},
    {
        "name": "Codex",
        "type": "agent",
        "role": "implementation, feasibility, architecture, execution details",
    },
    {
        "name": "Claude",
        "type": "agent",
        "role": "reasoning, critique, writing clarity, tradeoffs",
    },
    {
        "name": "Gemini",
        "type": "agent",
        "role": "ideation, alternatives, synthesis, reframing",
    },
]

DEFAULT_SETTINGS: dict[str, Any] = {
    "pollIntervalMs": 1500,
    "roomName": "main",
}

_append_lock = threading.Lock()


def storage_path(project_root: Path) -> Path:
    return project_root / STORAGE_DIRNAME


def sessions_dir(project_root: Path) -> Path:
    return storage_path(project_root) / "sessions"


def session_dir(project_root: Path, session_id: str) -> Path:
    return sessions_dir(project_root) / session_id


def current_session_pointer(project_root: Path) -> Path:
    return storage_path(project_root) / "current-session.json"


def _session_file(project_root: Path, session_id: str) -> Path:
    return session_dir(project_root, session_id) / "session.json"


def _participants_file(project_root: Path) -> Path:
    return storage_path(project_root) / "participants.json"


def _transcript_file(project_root: Path, session_id: str) -> Path:
    return session_dir(project_root, session_id) / "transcript.jsonl"


def _settings_file(project_root: Path) -> Path:
    return storage_path(project_root) / "settings.json"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="microseconds")


def _write_json_atomic(target: Path, payload: str) -> None:
    tmp = target.with_name(f"{target.name}.tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, target)


def _write_session_atomic(project_root: Path, session: Session) -> None:
    target = _session_file(project_root, session.id)
    _write_json_atomic(target, session.model_dump_json(indent=2))


def _write_pointer_atomic(project_root: Path, session_id: str) -> None:
    target = current_session_pointer(project_root)
    _write_json_atomic(target, json.dumps({"sessionId": session_id}, indent=2))


def _message_count(project_root: Path, session_id: str) -> int:
    transcript_file = _transcript_file(project_root, session_id)
    if not transcript_file.exists():
        return 0
    return sum(1 for line in transcript_file.read_text(encoding="utf-8").splitlines() if line.strip())


def _new_session(project_root: Path, title: str | None = None) -> Session:
    now = _now()
    normalized_title = title.strip() if title is not None and title.strip() else None
    return Session(
        id=f"sess-{uuid.uuid4().hex[:8]}",
        projectPath=str(project_root.resolve()),
        createdAt=now,
        updatedAt=now,
        roomName="main",
        title=normalized_title,
    )


def _migrate_legacy_layout_if_needed(project_root: Path) -> None:
    root = storage_path(project_root)
    legacy_session_file = root / "session.json"
    legacy_transcript_file = root / "transcript.jsonl"
    sessions_root = sessions_dir(project_root)

    if not legacy_session_file.exists() or not legacy_transcript_file.exists():
        return
    if any(sessions_root.iterdir()):
        return

    legacy_session = Session.model_validate_json(legacy_session_file.read_text(encoding="utf-8"))
    destination = session_dir(project_root, legacy_session.id)
    destination.mkdir(parents=True, exist_ok=True)
    os.replace(legacy_session_file, destination / "session.json")
    os.replace(legacy_transcript_file, destination / "transcript.jsonl")
    _write_pointer_atomic(project_root, legacy_session.id)


def init_storage(project_root: Path) -> None:
    root = storage_path(project_root)
    root.mkdir(parents=True, exist_ok=True)
    sessions_dir(project_root).mkdir(parents=True, exist_ok=True)

    participants_file = _participants_file(project_root)
    if not participants_file.exists():
        participants_file.write_text(
            json.dumps(DEFAULT_PARTICIPANTS, indent=2),
            encoding="utf-8",
        )

    settings_file = _settings_file(project_root)
    if not settings_file.exists():
        settings_file.write_text(
            json.dumps(DEFAULT_SETTINGS, indent=2),
            encoding="utf-8",
        )

    _migrate_legacy_layout_if_needed(project_root)


def get_current_session_id(project_root: Path) -> str | None:
    pointer_file = current_session_pointer(project_root)
    if not pointer_file.exists():
        return None
    try:
        payload = json.loads(pointer_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    session_id = payload.get("sessionId")
    return session_id if isinstance(session_id, str) and session_id.strip() else None


def set_current_session_id(project_root: Path, session_id: str) -> None:
    _write_pointer_atomic(project_root, session_id)


def create_session(project_root: Path, title: str | None = None) -> Session:
    session = _new_session(project_root, title=title)
    session_root = session_dir(project_root, session.id)
    session_root.mkdir(parents=True, exist_ok=True)
    _write_session_atomic(project_root, session)
    _transcript_file(project_root, session.id).touch(exist_ok=True)
    return session


def ensure_current_session(project_root: Path) -> Session:
    session_id = get_current_session_id(project_root)
    if session_id and session_dir(project_root, session_id).is_dir():
        return read_session(project_root, session_id=session_id)
    session = create_session(project_root, title=None)
    set_current_session_id(project_root, session.id)
    return session


def activate_session(project_root: Path, session_id: str) -> Session:
    if not session_dir(project_root, session_id).is_dir():
        raise KeyError(session_id)
    session = read_session(project_root, session_id=session_id)
    set_current_session_id(project_root, session_id)
    return session


def update_session_title(project_root: Path, session_id: str, title: str | None) -> Session:
    session = read_session(project_root, session_id=session_id)
    session.title = title.strip() if title is not None and title.strip() else None
    session.updatedAt = _now()
    _write_session_atomic(project_root, session)
    return session


def list_sessions(project_root: Path) -> list[SessionSummary]:
    summaries: list[SessionSummary] = []
    for candidate in sessions_dir(project_root).iterdir():
        if not candidate.is_dir():
            continue
        session_file = candidate / "session.json"
        if not session_file.exists():
            continue
        session = Session.model_validate_json(session_file.read_text(encoding="utf-8"))
        summaries.append(
            SessionSummary(
                id=session.id,
                title=session.title,
                createdAt=session.createdAt,
                updatedAt=session.updatedAt,
                messageCount=_message_count(project_root, session.id),
            )
        )
    return sorted(
        summaries,
        key=lambda session: (session.updatedAt, session.createdAt, session.id),
        reverse=True,
    )


def read_session(project_root: Path, session_id: str | None = None) -> Session:
    resolved_session_id = session_id or get_current_session_id(project_root)
    if not resolved_session_id:
        raise FileNotFoundError("No current session is set.")
    return Session.model_validate_json(
        _session_file(project_root, resolved_session_id).read_text(encoding="utf-8")
    )


def read_participants(project_root: Path) -> list[Participant]:
    data = json.loads(_participants_file(project_root).read_text(encoding="utf-8"))
    return [Participant.model_validate(item) for item in data]


def read_messages(project_root: Path, session_id: str | None = None) -> list[Message]:
    resolved_session_id = session_id or get_current_session_id(project_root)
    if not resolved_session_id:
        raise FileNotFoundError("No current session is set.")
    messages: list[Message] = []
    transcript_file = _transcript_file(project_root, resolved_session_id)
    if not transcript_file.exists():
        return messages
    for line in transcript_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            messages.append(Message.model_validate_json(line))
    return messages


def read_settings(project_root: Path) -> dict[str, Any]:
    return json.loads(_settings_file(project_root).read_text(encoding="utf-8"))

def append_message(
    project_root: Path,
    payload: MessageCreate,
    room_id: str | None = None,
) -> Message:
    with _append_lock:
        session_id = get_current_session_id(project_root)
        if not session_id:
            session = ensure_current_session(project_root)
            session_id = session.id
        else:
            session = read_session(project_root, session_id=session_id)

        message = Message(
            id=format_message_id(session.nextMessageId),
            roomId=room_id or session.roomName,
            sender=payload.sender,
            senderType=payload.senderType,
            text=payload.text,
            mentions=payload.mentions,
            replyTo=payload.replyTo,
            timestamp=_now(),
        )

        with _transcript_file(project_root, session_id).open("a", encoding="utf-8") as handle:
            handle.write(message.model_dump_json() + "\n")

        session.nextMessageId += 1
        session.updatedAt = _now()
        _write_session_atomic(project_root, session)
        return message
