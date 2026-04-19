from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def storage_dir(tmp_path: Path) -> Path:
    """Temporary project folder containing no .ai-boardroom yet."""
    return tmp_path


@pytest.fixture
def initialized_storage(storage_dir: Path) -> Path:
    """Temporary project folder with .ai-boardroom/ already initialized."""
    from backend.storage import ensure_current_session, init_storage

    init_storage(storage_dir)
    ensure_current_session(storage_dir)
    return storage_dir


@pytest.fixture
def legacy_storage(storage_dir: Path) -> Path:
    """Temporary project folder with the legacy flat storage layout pre-created."""
    from backend.schemas import Session
    from backend.storage import storage_path

    root = storage_path(storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    session = Session(
        id="sess-legacy01",
        projectPath=str(storage_dir.resolve()),
        createdAt="2026-04-19T10:00:00-05:00",
        updatedAt="2026-04-19T10:00:00-05:00",
        roomName="main",
        nextMessageId=2,
    )
    (root / "session.json").write_text(session.model_dump_json(indent=2), encoding="utf-8")
    (root / "transcript.jsonl").write_text(
        '{"id":"msg-001","roomId":"main","sender":"User","senderType":"human","text":"legacy","mentions":[],"replyTo":null,"timestamp":"2026-04-19T10:00:01-05:00"}\n',
        encoding="utf-8",
    )
    return storage_dir


@pytest.fixture
def client(initialized_storage: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from backend import main as backend_main

    monkeypatch.setattr(backend_main, "PROJECT_ROOT", initialized_storage)
    app = backend_main.create_app()
    with TestClient(app) as test_client:
        yield test_client
