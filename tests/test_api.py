import concurrent.futures

from fastapi.testclient import TestClient
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
