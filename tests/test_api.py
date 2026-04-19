import concurrent.futures

from fastapi.testclient import TestClient
from backend.storage import create_session, get_current_session_id, read_messages, set_current_session_id


def test_health_endpoint(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_get_session_returns_session(client: TestClient):
    resp = client.get("/api/session")
    assert resp.status_code == 200
    body = resp.json()
    assert body["roomName"] == "main"
    assert body["id"].startswith("sess-")


def test_get_participants_returns_defaults(client: TestClient):
    resp = client.get("/api/participants")
    assert resp.status_code == 200
    names = [participant["name"] for participant in resp.json()]
    assert names == ["User", "Codex", "Claude", "Gemini"]


def test_get_messages_empty_initially(client: TestClient):
    resp = client.get("/api/messages")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_sessions_returns_startup_current_session(client: TestClient, initialized_storage):
    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == get_current_session_id(initialized_storage)


def test_create_app_ensures_current_session_exists(initialized_storage):
    from backend import main as backend_main

    backend_main.PROJECT_ROOT = initialized_storage
    backend_main.create_app()
    assert get_current_session_id(initialized_storage) is not None


def test_get_sessions_returns_all_sessions_newest_first(client: TestClient, initialized_storage):
    first = create_session(initialized_storage, title="One")
    second = create_session(initialized_storage, title="Two")
    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    ids = [session["id"] for session in resp.json()]
    assert ids[:3] == [second.id, first.id, get_current_session_id(initialized_storage)]


def test_root_serves_frontend_index(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "AI Boardroom" in resp.text
    assert resp.headers["content-type"].startswith("text/html")


def test_post_message_persists_and_returns_stored(client: TestClient):
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


def test_post_message_then_get_messages_returns_it(client: TestClient):
    client.post(
        "/api/messages",
        json={"sender": "User", "senderType": "human", "text": "hi"},
    )
    resp = client.get("/api/messages")
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 1
    assert messages[0]["id"] == "msg-001"


def test_post_sessions_without_body_creates_and_activates(client: TestClient):
    original_id = client.get("/api/session").json()["id"]
    resp = client.post("/api/sessions")
    assert resp.status_code == 201
    created = resp.json()
    assert created["title"] is None
    assert created["id"] != original_id
    assert client.get("/api/session").json()["id"] == created["id"]
    listed_ids = [session["id"] for session in client.get("/api/sessions").json()]
    assert original_id in listed_ids


def test_post_sessions_with_title_persists_title(client: TestClient):
    resp = client.post("/api/sessions", json={"title": "API review"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "API review"


def test_post_sessions_with_empty_object_is_allowed(client: TestClient):
    resp = client.post("/api/sessions", json={})
    assert resp.status_code == 201
    assert resp.json()["title"] is None


def test_activate_known_session_switches_pointer_and_messages(client: TestClient, initialized_storage):
    first = client.get("/api/session").json()["id"]
    client.post("/api/messages", json={"sender": "User", "senderType": "human", "text": "first"})
    second = create_session(initialized_storage, title="Second")
    set_current_session_id(initialized_storage, second.id)
    client.post("/api/messages", json={"sender": "User", "senderType": "human", "text": "second"})
    resp = client.post(f"/api/sessions/{first}/activate")
    assert resp.status_code == 200
    messages = client.get("/api/messages").json()
    assert [message["text"] for message in messages] == ["first"]


def test_activate_unknown_session_returns_404(client: TestClient):
    resp = client.post("/api/sessions/sess-missing/activate")
    assert resp.status_code == 404


def test_patch_session_renames_current_session(client: TestClient):
    current = client.get("/api/session").json()
    resp = client.patch(f"/api/sessions/{current['id']}", json={"title": "API contract review"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "API contract review"
    assert client.get("/api/session").json()["title"] == "API contract review"


def test_patch_session_renames_non_current_session_without_switching(client: TestClient, initialized_storage):
    current = client.get("/api/session").json()
    other = create_session(initialized_storage, title="Old")
    resp = client.patch(f"/api/sessions/{other.id}", json={"title": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Renamed"
    assert client.get("/api/session").json()["id"] == current["id"]


def test_post_message_after_switch_appends_to_current_session(client: TestClient, initialized_storage):
    first_id = client.get("/api/session").json()["id"]
    second = create_session(initialized_storage, title="Second")
    client.post(f"/api/sessions/{second.id}/activate")
    resp = client.post("/api/messages", json={"sender": "User", "senderType": "human", "text": "new current"})
    assert resp.status_code == 201
    assert read_messages(initialized_storage, session_id=first_id) == []
    assert [message.text for message in read_messages(initialized_storage, session_id=second.id)] == ["new current"]


def test_post_message_rejects_empty_text(client: TestClient):
    resp = client.post(
        "/api/messages",
        json={"sender": "User", "senderType": "human", "text": ""},
    )
    assert resp.status_code == 422


def test_post_message_rejects_bad_sender_type(client: TestClient):
    resp = client.post(
        "/api/messages",
        json={"sender": "User", "senderType": "alien", "text": "hi"},
    )
    assert resp.status_code == 422


def test_post_message_concurrent_returns_unique_ids(client: TestClient):
    def post_one(i: int):
        return client.post(
            "/api/messages",
            json={
                "sender": ["User", "Codex", "Claude", "Gemini"][i % 4],
                "senderType": "human" if i % 4 == 0 else "agent",
                "text": f"msg {i}",
            },
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        responses = list(executor.map(post_one, range(20)))

    assert all(response.status_code == 201 for response in responses)
    ids = [response.json()["id"] for response in responses]
    assert len(set(ids)) == 20, f"duplicate IDs: {sorted(ids)}"
