# Phase 7 - Verification & CLI Prompts

**Prerequisites:** [Phase 6 — App Assembly & Styling](phase-6-app-assembly.md)
complete. The app must render and accept posted messages in Chrome.

**Phase Goal:** Lock the DOM contract with Playwright tests, author the three
CLI startup prompts, and run full manual validation covering persistence,
default agent API posting, optional composer posting, and reload durability.

**Completion Criteria:**

- `pytest tests/test_dom_contract.py -v` shows 4 passed
- `pytest -v` is green
- Three prompt files exist under `prompts/`
- Manual validation checklist below completes successfully

**Next Phase:** None. MVP complete.

---

## Task 20: DOM Contract Playwright Tests

**Files:**

- Create: `tests/test_dom_contract.py`

- [ ] **Step 1: Write Playwright tests**

Create `tests/test_dom_contract.py` with four end-to-end checks:

- participant strip exposes the expected participant names
- a human composer post renders the required message `data-*` attributes
- the room header exposes `data-room-name="main"`
- an optional composer post with `data-post-as` renders agent identity and
  resets to `"User"` after submit

- [ ] **Step 2: Run the DOM test file**

Run:

```powershell
pytest tests/test_dom_contract.py -v
```

Expected:

- If Phases 1 through 6 are complete, the tests should pass.
- If they fail, fix the corresponding DOM binding or frontend behavior before
  moving on.

---

## Task 21: Codex Startup Prompt

**Files:**

- Create: `prompts/codex-startup.md`

- [ ] **Step 1: Write the prompt**

The prompt must state:

- participant name is `Codex`
- DOM inspection is the primary read path
- `GET /api/messages` is the backup read path
- `POST /api/messages` is the default write path
- composer posting with `data-post-as="Codex"` is optional
- response criteria are mention-driven plus reply-driven
- the CLI should contribute implementation, feasibility, and execution detail

---

## Task 22: Claude Startup Prompt

**Files:**

- Create: `prompts/claude-startup.md`

- [ ] **Step 1: Write the prompt**

The prompt must state:

- participant name is `Claude`
- DOM inspection is the primary read path
- `GET /api/messages` is the backup read path
- `POST /api/messages` is the default write path
- composer posting with `data-post-as="Claude"` is optional
- response criteria are mention-driven plus reply-driven
- the CLI should contribute critique, writing clarity, and tradeoff analysis

---

## Task 23: Gemini Startup Prompt

**Files:**

- Create: `prompts/gemini-startup.md`

- [ ] **Step 1: Write the prompt**

The prompt must state:

- participant name is `Gemini`
- DOM inspection is the primary read path
- `GET /api/messages` is the backup read path
- `POST /api/messages` is the default write path
- composer posting with `data-post-as="Gemini"` is optional
- response criteria are mention-driven plus reply-driven
- the CLI should contribute ideation, alternatives, and synthesis

---

## Task 24: End-to-End Manual Validation

**Files:** none

- [ ] **Step 1: Start the application**

Run:

```powershell
.\setup.ps1
.\run.ps1
```

Expected:

- Uvicorn starts on port `8765`
- frontend assets are served locally
- the app loads without a CDN dependency for Vue

- [ ] **Step 2: Verify frontend bootstrap**

Open `http://127.0.0.1:8765/` in Chrome.

Expected:

- two-column layout renders
- sidebar shows session metadata and project path
- participant strip shows `User`, `Codex`, `Claude`, and `Gemini`
- empty-state text is visible before the first message

- [ ] **Step 3: Post a user message via the composer**

Type `@all hello boardroom` in the composer and submit.

Expected:

- a new message appears from `User`
- DOM shows `data-sender="User"`, `data-mentions="all"`,
  `data-message-id="msg-001"`
- the composer clears
- `.composer.dataset.postAs` remains `"User"`

- [ ] **Step 4: Simulate an agent post via the default API path**

From a second PowerShell window:

```powershell
$body = @{
    sender = "Codex"
    senderType = "agent"
    text = "Acknowledged. Standing by."
    mentions = @("user")
    replyTo = "msg-001"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/api/messages -ContentType "application/json" -Body $body
```

Expected:

- within about 1.5 seconds the message appears without a reload
- DOM shows `data-sender="Codex"`, `data-reply-to="msg-001"`,
  `data-message-id="msg-002"`

- [ ] **Step 4a: Simulate an agent post via the optional composer path**

In Chrome DevTools on the open AI Boardroom tab:

```javascript
const form = document.querySelector(".composer");
form.dataset.postAs = "Gemini";
const input = form.querySelector(".composer-input");
input.value = "@user gemini here";
input.dispatchEvent(new Event("input", { bubbles: true }));
form.querySelector(".composer-send").click();
```

Expected:

- a new message appears with `data-sender="Gemini"`,
  `data-sender-type="agent"`, `data-message-id="msg-003"`
- after submit, `document.querySelector(".composer").dataset.postAs` is back to
  `"User"`

- [ ] **Step 5: Verify persistence**

Stop Uvicorn, restart with `.\run.ps1`, and reload Chrome.

Expected:

- all three messages remain visible
- `.ai-boardroom/transcript.jsonl` contains three lines
- `.ai-boardroom/session.json::nextMessageId` equals `4`

- [ ] **Step 5a: Verify concurrency safety end-to-end**

From PowerShell while the server is running:

```powershell
1..20 | ForEach-Object -Parallel {
    $body = @{ sender = "Codex"; senderType = "agent"; text = "stress $_" } | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/api/messages -ContentType "application/json" -Body $body
} -ThrottleLimit 10 | Select-Object -ExpandProperty id | Sort-Object -Unique | Measure-Object | Select-Object -ExpandProperty Count
```

Expected:

- the command prints `20`

- [ ] **Step 6: Run the full test suite**

Run:

```powershell
pytest -v
```

Expected:

- all backend and DOM contract tests pass

- [ ] **Step 7: Update docs after validation**

Once the manual pass is complete:

- update `docs/agent-compatibility-matrix.md` with validated cells
- keep `README.md` aligned with the actual implemented repo state
