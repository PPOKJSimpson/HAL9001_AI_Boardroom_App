import os
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright.sync_playwright


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _get_json(url: str) -> dict | list:
    with urllib.request.urlopen(url, timeout=2) as response:
        return json.loads(response.read().decode("utf-8"))


def _wait_until(assertion, timeout_seconds: float = 5.0, interval_seconds: float = 0.1):
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            return assertion()
        except AssertionError as error:
            last_error = error
            time.sleep(interval_seconds)
    if last_error is not None:
        raise last_error
    raise TimeoutError("condition was not satisfied before timeout")


@pytest.fixture
def live_server(tmp_path: Path):
    port = _free_port()
    repo_root = Path(__file__).resolve().parent.parent
    env = {
        **os.environ,
        "PYTHONPATH": str(repo_root),
    }
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(tmp_path),
        env=env,
    )

    try:
        for _ in range(40):
            try:
                urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/api/health",
                    timeout=0.5,
                )
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("server did not start")

        yield f"http://127.0.0.1:{port}"
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_participant_strip_exposes_attributes(live_server: str):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        page.wait_for_selector(".participant-chip")
        names = page.eval_on_selector_all(
            ".participant-chip",
            "els => els.map(e => e.dataset.participantName)",
        )
        assert names == ["User", "Codex", "Claude", "Gemini"]
        browser.close()


def test_posted_message_exposes_contract_attributes(live_server: str):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        page.wait_for_selector(".composer-input")
        page.fill(".composer-input", "@codex please review")
        page.click(".composer-send")
        page.wait_for_selector("article.message")
        attrs = page.eval_on_selector(
            "article.message",
            """el => ({
                messageId: el.dataset.messageId,
                sender: el.dataset.sender,
                senderType: el.dataset.senderType,
                mentions: el.dataset.mentions,
                replyTo: el.dataset.replyTo,
                timestamp: el.dataset.timestamp,
            })""",
        )
        assert attrs["messageId"] == "msg-001"
        assert attrs["sender"] == "User"
        assert attrs["senderType"] == "human"
        assert attrs["mentions"] == "codex"
        assert attrs["replyTo"] == ""
        assert attrs["timestamp"]
        browser.close()


def test_room_header_exposes_room_name(live_server: str):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        page.wait_for_selector(".room-header")
        room_name = page.eval_on_selector(
            ".room-header",
            "el => el.dataset.roomName",
        )
        assert room_name == "main"
        browser.close()


def test_composer_data_post_as_produces_agent_identified_message(live_server: str):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        page.wait_for_selector(".composer")

        page.eval_on_selector(
            ".composer",
            "el => { el.dataset.postAs = 'Codex'; }",
        )
        page.fill(".composer-input", "@user codex here")
        page.click(".composer-send")
        page.wait_for_selector("article.message")

        attrs = page.eval_on_selector(
            "article.message",
            """el => ({
                sender: el.dataset.sender,
                senderType: el.dataset.senderType,
            })""",
        )
        assert attrs["sender"] == "Codex"
        assert attrs["senderType"] == "agent"

        reset_value = page.eval_on_selector(
            ".composer",
            "el => el.dataset.postAs",
        )
        assert reset_value == "User"
        browser.close()


def test_session_switch_flow_resets_message_ids_per_session(live_server: str):
    initial_session = _get_json(f"{live_server}/api/session")
    initial_session_id = initial_session["id"]
    initial_session_title = initial_session.get("title") or initial_session_id
    first_message = "session-one message"
    second_message = "session-two message"

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)

        page.wait_for_selector(".session-sidebar")
        sidebar_text = page.locator(".session-sidebar").inner_text()
        assert initial_session_id in sidebar_text

        page.fill(".composer-input", first_message)
        page.click(".composer-send")
        page.wait_for_selector('article.message[data-message-id="msg-001"]')
        assert first_message in page.locator("article.message .message-body").first.inner_text()

        page.click(".session-new-btn")
        page.wait_for_selector(".empty-room")
        assert page.locator("article.message").count() == 0

        current_session = _get_json(f"{live_server}/api/session")
        assert current_session["id"] != initial_session_id

        page.fill(".composer-input", second_message)
        page.click(".composer-send")
        page.wait_for_selector('article.message[data-message-id="msg-001"]')
        current_body = page.locator("article.message .message-body").first.inner_text()
        assert current_body == second_message

        page.locator(".past-session-row", has_text=initial_session_title).click()
        page.wait_for_function(
            """expectedText => {
                const body = document.querySelector("article.message .message-body");
                return body && body.textContent.includes(expectedText);
            }""",
            arg=first_message,
        )
        restored_body = page.locator("article.message .message-body").first.inner_text()
        assert restored_body == first_message

        restored_session = _get_json(f"{live_server}/api/session")
        assert restored_session["id"] == initial_session_id
        browser.close()


def test_renaming_current_session_updates_api_session_title(live_server: str):
    renamed_title = "Boardroom Session Renamed"

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)

        page.wait_for_selector(".session-title-input")
        title_input = page.locator(".session-title-input")
        title_input.fill(renamed_title)
        title_input.press("Enter")

        def _assert_title_updated():
            session = _get_json(f"{live_server}/api/session")
            assert session["title"] == renamed_title
            return session

        session = _wait_until(_assert_title_updated)
        assert session["title"] == renamed_title
        assert title_input.input_value() == renamed_title
        browser.close()
