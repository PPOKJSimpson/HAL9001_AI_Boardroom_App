from importlib import import_module
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api")

MessageCreate = import_module("backend.schemas").MessageCreate


class CreateSessionRequest(BaseModel):
    title: str | None = None


class UpdateSessionRequest(BaseModel):
    title: str | None = None


def _storage():
    return import_module("backend.storage")


def get_project_root() -> Path:
    from backend.main import PROJECT_ROOT

    return PROJECT_ROOT


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/session")
def get_session(root: Path = Depends(get_project_root)) -> dict:
    return _storage().read_session(root).model_dump()


@router.get("/sessions")
def get_sessions(root: Path = Depends(get_project_root)) -> list[dict]:
    return [session.model_dump() for session in _storage().list_sessions(root)]


@router.get("/participants")
def get_participants(root: Path = Depends(get_project_root)) -> list[dict]:
    return [participant.model_dump() for participant in _storage().read_participants(root)]


@router.get("/messages")
def get_messages(root: Path = Depends(get_project_root)) -> list[dict]:
    return [message.model_dump() for message in _storage().read_messages(root)]


@router.post("/messages", status_code=status.HTTP_201_CREATED)
def post_message(payload: MessageCreate, root: Path = Depends(get_project_root)) -> dict:
    session = _storage().read_session(root)
    stored = _storage().append_message(root, payload, room_id=session.roomName)
    return stored.model_dump()


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def post_session(
    payload: CreateSessionRequest | None = Body(default=None),
    root: Path = Depends(get_project_root),
) -> dict:
    title = payload.title if payload else None
    session = _storage().create_session(root, title=title)
    _storage().activate_session(root, session.id)
    return session.model_dump()


@router.post("/sessions/{session_id}/activate")
def activate_session(session_id: str, root: Path = Depends(get_project_root)) -> dict:
    try:
        session = _storage().activate_session(root, session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown session: {session_id}") from exc
    return session.model_dump()


@router.patch("/sessions/{session_id}")
def patch_session(
    session_id: str,
    payload: UpdateSessionRequest,
    root: Path = Depends(get_project_root),
) -> dict:
    try:
        session = _storage().update_session_title(root, session_id, payload.title)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown session: {session_id}") from exc
    return session.model_dump()
