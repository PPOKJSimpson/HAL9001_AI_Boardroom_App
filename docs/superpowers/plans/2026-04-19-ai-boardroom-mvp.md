# AI Boardroom MVP Implementation Plan - Index

> For agentic workers: phase files use checkbox tracking. Execute phases in
> order and do not mark a later phase complete until the earlier phase's
> completion criteria are met.

**Goal:** Build a local Teams-style web chat room where one human user and the
`Codex`, `Claude`, and `Gemini` CLIs share one channel, with project-local
persistence, a machine-readable DOM, and a local HTTP post API.

**Architecture:** A FastAPI backend serves a Vue 3 frontend with no frontend
build step. Vue is vendored locally under `frontend/vendor/` by `setup.ps1`;
runtime should not depend on a CDN. The backend exposes a small JSON API for
session metadata, participants, and messages. All state lives in a
project-local `.ai-boardroom/` directory using JSON for session,
participant, and settings data plus JSONL for append-only transcript history.
Message IDs are allocated from `session.json::nextMessageId` under a
`threading.Lock` so concurrent agent posts cannot collide. The frontend polls
the API to refresh messages and renders each message with stable `data-*`
attributes so CLIs with browser tooling can read the same room surface the
human sees.

**Agent I/O contract (authoritative):** see
[ADR 0001](../../adr/0001-agent-read-write-contract.md). DOM inspection is the
primary read surface for CLIs. `GET /api/messages` is the backup read path.
Humans write via the composer UI. Agents write by default via
`POST /api/messages` and may optionally write through the composer by setting
`data-post-as` when their harness supports browser automation. Per-CLI
validation is tracked in the
[agent compatibility matrix](../../agent-compatibility-matrix.md).

**Tech Stack:**

- Backend: Python 3.11+, FastAPI, Uvicorn, Pydantic v2
- Frontend: Vue 3 via vendored ESM module, vanilla JS modules, CSS
- Storage: JSON + JSONL under `.ai-boardroom/`
- Testing: pytest + httpx for backend, Playwright for frontend DOM contract
- Target OS: Windows 11, PowerShell launch scripts

---

## Phase Overview

Each phase delivers a self-contained, testable milestone.

| # | Phase | Tasks | Deliverable |
|---|---|---:|---|
| 1 | [Foundation](2026-04-19-ai-boardroom-mvp/phase-1-foundation.md) | 3 | Dependencies installed, schemas and ID generator tested |
| 2 | [Storage Layer](2026-04-19-ai-boardroom-mvp/phase-2-storage.md) | 3 | `.ai-boardroom/` initialization, reads, and appends round-trip through tests |
| 3 | [HTTP API](2026-04-19-ai-boardroom-mvp/phase-3-api.md) | 3 | FastAPI serves `/api/session`, `/api/participants`, `GET /api/messages`, and `POST /api/messages` |
| 4 | [Frontend Delivery & API Client](2026-04-19-ai-boardroom-mvp/phase-4-frontend-delivery.md) | 3 | Uvicorn serves the placeholder page, `setup.ps1` and `run.ps1` exist, browser reaches the API |
| 5 | [Frontend Components](2026-04-19-ai-boardroom-mvp/phase-5-frontend-components.md) | 5 | Vue components render the DOM contract attributes |
| 6 | [App Assembly & Styling](2026-04-19-ai-boardroom-mvp/phase-6-app-assembly.md) | 2 | Working styled UI end-to-end in Chrome |
| 7 | [Verification & CLI Prompts](2026-04-19-ai-boardroom-mvp/phase-7-verification.md) | 5 | Playwright DOM tests pass, startup prompts exist, manual validation completed |

**Total:** 24 tasks across 7 phases.

---

## File Structure

### Backend

- `backend/__init__.py` package marker
- `backend/main.py` FastAPI app, static mount, router include, localhost CORS
- `backend/api.py` route handlers for `/api/session`, `/api/messages`, `/api/participants`
- `backend/storage.py` `.ai-boardroom/` initialization and file I/O helpers
- `backend/schemas.py` Pydantic models for session, participants, and messages
- `backend/ids.py` monotonic message ID generator

### Frontend

- `frontend/index.html` document shell, vendored Vue import, root mount
- `frontend/app.js` Vue bootstrap, state, polling loop
- `frontend/api.js` fetch-based API client
- `frontend/components/MessageItem.js` single message article with DOM contract
- `frontend/components/MessageList.js` ordered message column
- `frontend/components/Composer.js` input and submit button
- `frontend/components/RoomHeader.js` room title and participant strip
- `frontend/components/ParticipantStrip.js` participant chips
- `frontend/components/SessionSidebar.js` session info panel
- `frontend/styles/brutalist.css` app styling

### Tests

- `tests/__init__.py`
- `tests/conftest.py` fixtures for temp `.ai-boardroom/` dirs and test client
- `tests/test_schemas.py`
- `tests/test_storage.py`
- `tests/test_ids.py`
- `tests/test_api.py`
- `tests/test_dom_contract.py`

### Prompts

- `prompts/codex-startup.md`
- `prompts/claude-startup.md`
- `prompts/gemini-startup.md`

### Tooling

- `requirements.txt` runtime and test dependencies
- `setup.ps1` one-time bootstrap: venv, deps, Playwright browser, vendored Vue
- `run.ps1` activate venv and start Uvicorn
- `frontend/vendor/vue.esm-browser.prod.js` vendored Vue runtime created by `setup.ps1`
- `.gitignore` excludes `.ai-boardroom/`, caches, and vendored runtime artifacts
- `pytest.ini` test discovery configuration

### Docs referenced by this plan

- `README.md` bootstrap, run, and test guidance
- `docs/adr/0001-agent-read-write-contract.md` authoritative agent contract
- `docs/agent-compatibility-matrix.md` per-CLI capability tracking

---

## Spec Coverage

- Storage layout under `.ai-boardroom/`: Phase 2
- API endpoints: Phase 3
- DOM contract: Phases 5 and 7
- Frontend layout and styling: Phases 5 and 6
- Startup prompts for `Codex`, `Claude`, and `Gemini`: Phase 7
- Polling-based updates: Phase 6
- Manual-first workflow: Phase 7
- Addressing conventions: Phases 5 and 7

## Non-goals

- No auth
- No MCP transport
- No turn coordination
- No CLI process launching
- No threaded UI

## Deferred Items

- WebSockets or SSE
- Multiple rooms
- Attachments
- Presence
- Prompt templates
- Wrapper CLIs
