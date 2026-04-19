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
    from backend.storage import init_storage

    init_storage(storage_dir)
    return storage_dir


@pytest.fixture
def client(initialized_storage: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from backend import main as backend_main

    monkeypatch.setattr(backend_main, "PROJECT_ROOT", initialized_storage)
    app = backend_main.create_app()
    with TestClient(app) as test_client:
        yield test_client
