# Phase 1 — Foundation

**Prerequisites:** None. This is the starting phase.

**Phase Goal:** Install dependencies, create project scaffolding, and land the two pieces of pure logic (Pydantic schemas, ID generator) that the rest of the backend depends on.

**Completion Criteria:**
- `pip install -r requirements.txt` succeeds in a fresh venv
- `pytest --version` prints 8.3.x
- `pytest tests/test_schemas.py tests/test_ids.py -v` shows 10 PASSED
- `git log` shows 3 commits on this phase

**Next Phase:** [Phase 2 — Storage Layer](phase-2-storage.md)

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `pytest.ini`
- Create: `backend/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
playwright==1.47.0
pytest-playwright==0.5.2
```

- [ ] **Step 2: Create `.gitignore`**

```
.ai-boardroom/
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
node_modules/
.playwright/
test-results/
frontend/vendor/
```

- [ ] **Step 3: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

- [ ] **Step 4: Create empty package markers**

Create `backend/__init__.py` with a single empty line.
Create `tests/__init__.py` with a single empty line.

- [ ] **Step 5: Install dependencies and verify pytest runs**

Run (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
pytest --version
```

Expected: pytest version prints (8.3.x), no errors.

- [ ] **Step 6: Commit**

```bash
git init
git add requirements.txt .gitignore pytest.ini backend/__init__.py tests/__init__.py
git commit -m "chore: scaffold project with pytest and deps"
```

---

## Task 2: Pydantic Schemas

**Files:**
- Create: `backend/schemas.py`
- Test: `tests/test_schemas.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_schemas.py`:

```python
import pytest
from pydantic import ValidationError
from backend.schemas import Message, MessageCreate, Participant, Session


def test_message_create_accepts_valid_payload():
    m = MessageCreate(
        sender="Gemini",
        senderType="agent",
        text="Hello room.",
        mentions=["codex"],
        replyTo=None,
    )
    assert m.sender == "Gemini"
    assert m.senderType == "agent"
    assert m.mentions == ["codex"]


def test_message_create_defaults_mentions_and_reply_to():
    m = MessageCreate(sender="User", senderType="human", text="hi")
    assert m.mentions == []
    assert m.replyTo is None


def test_message_create_rejects_empty_text():
    with pytest.raises(ValidationError):
        MessageCreate(sender="User", senderType="human", text="")


def test_message_create_rejects_invalid_sender_type():
    with pytest.raises(ValidationError):
        MessageCreate(sender="User", senderType="alien", text="hi")


def test_message_includes_server_generated_fields():
    m = Message(
        id="msg-001",
        roomId="main",
        sender="User",
        senderType="human",
        text="hi",
        mentions=[],
        replyTo=None,
        timestamp="2026-04-19T14:32:10-05:00",
    )
    assert m.id == "msg-001"
    assert m.roomId == "main"


def test_participant_requires_name_and_type():
    p = Participant(name="Claude", type="agent", role="reasoning")
    assert p.name == "Claude"
    with pytest.raises(ValidationError):
        Participant(name="Claude")  # type: ignore


def test_session_has_required_fields():
    s = Session(
        id="sess-abc",
        projectPath="C:/projects/ai-boardroom",
        createdAt="2026-04-19T14:00:00-05:00",
        updatedAt="2026-04-19T14:00:00-05:00",
        roomName="main",
    )
    assert s.roomName == "main"


def test_session_defaults_next_message_id_to_one():
    s = Session(
        id="sess-abc",
        projectPath=".",
        createdAt="2026-04-19T14:00:00-05:00",
        updatedAt="2026-04-19T14:00:00-05:00",
        roomName="main",
    )
    assert s.nextMessageId == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_schemas.py -v`
Expected: `ModuleNotFoundError: No module named 'backend.schemas'` or all tests FAIL.

- [ ] **Step 3: Implement schemas**

Create `backend/schemas.py`:

```python
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

SenderType = Literal["human", "agent", "system"]


class MessageCreate(BaseModel):
    sender: str
    senderType: SenderType
    text: str
    mentions: List[str] = Field(default_factory=list)
    replyTo: Optional[str] = None

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        return v


class Message(MessageCreate):
    id: str
    roomId: str
    timestamp: str


class Participant(BaseModel):
    name: str
    type: SenderType
    role: Optional[str] = None


class Session(BaseModel):
    id: str
    projectPath: str
    createdAt: str
    updatedAt: str
    roomName: str
    nextMessageId: int = 1
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_schemas.py -v`
Expected: 8 PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/schemas.py tests/test_schemas.py
git commit -m "feat: add Pydantic schemas for message, participant, session"
```

---

## Task 3: Message ID Generator

**Files:**
- Create: `backend/ids.py`
- Test: `tests/test_ids.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_ids.py`:

```python
from backend.ids import format_message_id, next_message_id_from_count


def test_format_message_id_pads_to_three_digits():
    assert format_message_id(1) == "msg-001"
    assert format_message_id(42) == "msg-042"
    assert format_message_id(104) == "msg-104"


def test_format_message_id_allows_four_digits():
    assert format_message_id(1000) == "msg-1000"


def test_next_message_id_from_count_increments():
    assert next_message_id_from_count(0) == "msg-001"
    assert next_message_id_from_count(3) == "msg-004"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ids.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement ID generator**

Create `backend/ids.py`:

```python
def format_message_id(n: int) -> str:
    return f"msg-{n:03d}"


def next_message_id_from_count(existing_count: int) -> str:
    return format_message_id(existing_count + 1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ids.py -v`
Expected: 3 PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/ids.py tests/test_ids.py
git commit -m "feat: add monotonic message ID generator"
```
