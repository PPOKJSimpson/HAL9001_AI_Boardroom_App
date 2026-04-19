import os
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
