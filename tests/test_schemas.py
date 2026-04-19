import pytest
from pydantic import ValidationError

from backend.schemas import Message, MessageCreate, Participant, Session, SessionSummary


def test_message_create_accepts_valid_payload():
    message = MessageCreate(
        sender="Gemini",
        senderType="agent",
        text="Hello room.",
        mentions=["codex"],
        replyTo=None,
    )
    assert message.sender == "Gemini"
    assert message.senderType == "agent"
    assert message.mentions == ["codex"]


def test_message_create_defaults_mentions_and_reply_to():
    message = MessageCreate(sender="User", senderType="human", text="hi")
    assert message.mentions == []
    assert message.replyTo is None


def test_message_create_rejects_empty_text():
    with pytest.raises(ValidationError):
        MessageCreate(sender="User", senderType="human", text="")


def test_message_create_rejects_invalid_sender_type():
    with pytest.raises(ValidationError):
        MessageCreate(sender="User", senderType="alien", text="hi")


def test_message_includes_server_generated_fields():
    message = Message(
        id="msg-001",
        roomId="main",
        sender="User",
        senderType="human",
        text="hi",
        mentions=[],
        replyTo=None,
        timestamp="2026-04-19T14:32:10-05:00",
    )
    assert message.id == "msg-001"
    assert message.roomId == "main"


def test_participant_requires_name_and_type():
    participant = Participant(name="Claude", type="agent", role="reasoning")
    assert participant.name == "Claude"
    with pytest.raises(ValidationError):
        Participant(name="Claude")  # type: ignore[call-arg]


def test_session_has_required_fields():
    session = Session(
        id="sess-abc",
        projectPath="C:/projects/ai-boardroom",
        createdAt="2026-04-19T14:00:00-05:00",
        updatedAt="2026-04-19T14:00:00-05:00",
        roomName="main",
    )
    assert session.roomName == "main"
    assert session.title is None


def test_session_defaults_next_message_id_to_one():
    session = Session(
        id="sess-abc",
        projectPath=".",
        createdAt="2026-04-19T14:00:00-05:00",
        updatedAt="2026-04-19T14:00:00-05:00",
        roomName="main",
    )
    assert session.nextMessageId == 1


def test_session_title_round_trips_json():
    session = Session(
        id="sess-abc",
        projectPath=".",
        createdAt="2026-04-19T14:00:00-05:00",
        updatedAt="2026-04-19T14:00:00-05:00",
        roomName="main",
        title="API review",
    )
    restored = Session.model_validate_json(session.model_dump_json())
    assert restored.title == "API review"


def test_session_summary_requires_core_fields_and_defaults_title():
    summary = SessionSummary(
        id="sess-abc",
        createdAt="2026-04-19T14:00:00-05:00",
        updatedAt="2026-04-19T14:05:00-05:00",
        messageCount=3,
    )
    assert summary.title is None
    with pytest.raises(ValidationError):
        SessionSummary(id="sess-abc", createdAt="x", updatedAt="y")  # type: ignore[call-arg]
