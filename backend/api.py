from importlib import import_module
from pathlib import Path

from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/api")

MessageCreate = import_module("backend.schemas").MessageCreate


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
