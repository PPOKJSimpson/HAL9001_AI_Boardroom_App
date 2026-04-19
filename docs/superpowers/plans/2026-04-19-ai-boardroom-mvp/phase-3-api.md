# Phase 3 — HTTP API

**Prerequisites:** [Phase 2 — Storage Layer](phase-2-storage.md) complete. `append_message`, `read_session`, `read_participants`, `read_messages` must all import and pass tests.

**Phase Goal:** Build the FastAPI application skeleton and expose all four MVP endpoints (`GET /api/session`, `GET /api/participants`, `GET /api/messages`, `POST /api/messages`) with full integration-test coverage using `TestClient`.

**Completion Criteria:**
- `pytest tests/test_api.py -v` shows 9 PASSED (includes concurrent-POST uniqueness test)
- All endpoints return correct JSON against a fresh `.ai-boardroom/` fixture
- `POST /api/messages` rejects empty text and invalid sender types with 422
- 20 parallel POSTs produce 20 distinct message IDs

**Next Phase:** [Phase 4 — Frontend Delivery & API Client](phase-4-frontend-delivery.md)

---

## Task 7: FastAPI App Skeleton and Dependency

**Files:**
- Create: `backend/main.py`
- Create: `backend/api.py`
- Modify: `tests/conftest.py` (add TestClient fixture)
- Test: `tests/test_api.py`

- [ ] **Step 1: Extend conftest.py with an API client fixture**

Append to `tests/conftest.py`:

```python
from fastapi.testclient import TestClient


@pytest.fixture
def client(initialized_storage, monkeypatch):
    from backend import main as backend_main
    monkeypatch.setattr(backend_main, "PROJECT_ROOT", initialized_storage)
    app = backend_main.create_app()
    with TestClient(app) as c:
        yield c
```

- [ ] **Step 2: Write failing health/session tests**

Create `tests/test_api.py`:

```python
def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_get_session_returns_session(client):
    resp = client.get("/api/session")
    assert resp.status_code == 200
    body = resp.json()
    assert body["roomName"] == "main"
    assert body["id"].startswith("sess-")
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v`
Expected: `ModuleNotFoundError: No module named 'backend.main'`.

- [ ] **Step 4: Implement main.py and api.py**

Create `backend/api.py`:

```python
from fastapi import APIRouter, Depends
from pathlib import Path

from backend import storage

router = APIRouter(prefix="/api")


def get_project_root() -> Path:
    from backend.main import PROJECT_ROOT
    return PROJECT_ROOT


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/session")
def get_session(root: Path = Depends(get_project_root)) -> dict:
    return storage.read_session(root).model_dump()
```

Create `backend/main.py`:

```python
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import storage
from backend.api import router as api_router

PROJECT_ROOT: Path = Path.cwd()


def create_app() -> FastAPI:
    storage.init_storage(PROJECT_ROOT)
    app = FastAPI(title="AI Boardroom", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://127.0.0.1"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_api.py -v`
Expected: 2 PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/main.py backend/api.py tests/conftest.py tests/test_api.py
git commit -m "feat: FastAPI skeleton with /api/health and /api/session"
```

---

## Task 8: Participants and Messages GET Endpoints

**Files:**
- Modify: `backend/api.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_api.py`:

```python
def test_get_participants_returns_defaults(client):
    resp = client.get("/api/participants")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert names == ["User", "Codex", "Claude", "Gemini"]


def test_get_messages_empty_initially(client):
    resp = client.get("/api/messages")
    assert resp.status_code == 200
    assert resp.json() == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v`
Expected: 2 new FAILs (404 responses).

- [ ] **Step 3: Implement endpoints**

Append to `backend/api.py`:

```python
@router.get("/participants")
def get_participants(root: Path = Depends(get_project_root)) -> list[dict]:
    return [p.model_dump() for p in storage.read_participants(root)]


@router.get("/messages")
def get_messages(root: Path = Depends(get_project_root)) -> list[dict]:
    return [m.model_dump() for m in storage.read_messages(root)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api.py -v`
Expected: 4 PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/api.py tests/test_api.py
git commit -m "feat: GET /api/participants and /api/messages"
```

---

## Task 9: POST /api/messages

**Files:**
- Modify: `backend/api.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_api.py`:

```python
def test_post_message_persists_and_returns_stored(client):
    body = {
        "sender": "User",
        "senderType": "human",
        "text": "hello room",
        "mentions": ["codex"],
        "replyTo": None,
    }
    resp = client.post("/api/messages", json=body)
    assert resp.status_code == 201
    stored = resp.json()
    assert stored["id"] == "msg-001"
    assert stored["sender"] == "User"
    assert stored["text"] == "hello room"
    assert stored["timestamp"]


def test_post_message_then_get_messages_returns_it(client):
    client.post(
        "/api/messages",
        json={"sender": "User", "senderType": "human", "text": "hi"},
    )
    resp = client.get("/api/messages")
    assert resp.status_code == 200
    msgs = resp.json()
    assert len(msgs) == 1
    assert msgs[0]["id"] == "msg-001"


def test_post_message_rejects_empty_text(client):
    resp = client.post(
        "/api/messages",
        json={"sender": "User", "senderType": "human", "text": ""},
    )
    assert resp.status_code == 422


def test_post_message_rejects_bad_sender_type(client):
    resp = client.post(
        "/api/messages",
        json={"sender": "User", "senderType": "alien", "text": "hi"},
    )
    assert resp.status_code == 422


def test_post_message_concurrent_returns_unique_ids(client):
    """Simulate 3 agents + user posting near-simultaneously.
    All must get distinct IDs and 201 status."""
    import concurrent.futures

    def post_one(i: int):
        return client.post(
            "/api/messages",
            json={
                "sender": ["User", "Codex", "Claude", "Gemini"][i % 4],
                "senderType": "human" if i % 4 == 0 else "agent",
                "text": f"msg {i}",
            },
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        responses = list(ex.map(post_one, range(20)))

    assert all(r.status_code == 201 for r in responses)
    ids = [r.json()["id"] for r in responses]
    assert len(set(ids)) == 20, f"duplicate IDs: {sorted(ids)}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v -k post_message`
Expected: 5 FAILs (405 Method Not Allowed).

- [ ] **Step 3: Implement POST endpoint**

Append to `backend/api.py`:

```python
from fastapi import status
from backend.schemas import MessageCreate


@router.post("/messages", status_code=status.HTTP_201_CREATED)
def post_message(
    payload: MessageCreate, root: Path = Depends(get_project_root)
) -> dict:
    session = storage.read_session(root)
    stored = storage.append_message(root, payload, room_id=session.roomName)
    return stored.model_dump()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api.py -v`
Expected: 9 PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/api.py tests/test_api.py
git commit -m "feat: POST /api/messages persists to transcript.jsonl"
```
