import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.ids import format_message_id
from backend.schemas import Message, MessageCreate, Participant, Session

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


def _session_file(project_root: Path) -> Path:
    return storage_path(project_root) / "session.json"


def _participants_file(project_root: Path) -> Path:
    return storage_path(project_root) / "participants.json"


def _transcript_file(project_root: Path) -> Path:
    return storage_path(project_root) / "transcript.jsonl"


def _settings_file(project_root: Path) -> Path:
    return storage_path(project_root) / "settings.json"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def init_storage(project_root: Path) -> None:
    root = storage_path(project_root)
    root.mkdir(parents=True, exist_ok=True)

    session_file = _session_file(project_root)
    if not session_file.exists():
        now = _now()
        session = Session(
            id=f"sess-{uuid.uuid4().hex[:8]}",
            projectPath=str(project_root.resolve()),
            createdAt=now,
            updatedAt=now,
            roomName="main",
        )
        session_file.write_text(session.model_dump_json(indent=2), encoding="utf-8")

    participants_file = _participants_file(project_root)
    if not participants_file.exists():
        participants_file.write_text(
            json.dumps(DEFAULT_PARTICIPANTS, indent=2),
            encoding="utf-8",
        )

    transcript_file = _transcript_file(project_root)
    if not transcript_file.exists():
        transcript_file.touch()

    settings_file = _settings_file(project_root)
    if not settings_file.exists():
        settings_file.write_text(
            json.dumps(DEFAULT_SETTINGS, indent=2),
            encoding="utf-8",
        )


def read_session(project_root: Path) -> Session:
    return Session.model_validate_json(_session_file(project_root).read_text(encoding="utf-8"))


def read_participants(project_root: Path) -> list[Participant]:
    data = json.loads(_participants_file(project_root).read_text(encoding="utf-8"))
    return [Participant.model_validate(item) for item in data]


def read_messages(project_root: Path) -> list[Message]:
    messages: list[Message] = []
    for line in _transcript_file(project_root).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            messages.append(Message.model_validate_json(line))
    return messages


def read_settings(project_root: Path) -> dict[str, Any]:
    return json.loads(_settings_file(project_root).read_text(encoding="utf-8"))


def _write_session_atomic(project_root: Path, session: Session) -> None:
    target = _session_file(project_root)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(session.model_dump_json(indent=2), encoding="utf-8")
    os.replace(tmp, target)


def append_message(
    project_root: Path,
    payload: MessageCreate,
    room_id: str = "main",
) -> Message:
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

        with _transcript_file(project_root).open("a", encoding="utf-8") as handle:
            handle.write(message.model_dump_json() + "\n")

        session.nextMessageId += 1
        session.updatedAt = _now()
        _write_session_atomic(project_root, session)
        return message
