# AI Boardroom

A local, Teams-style meeting room for one human user plus multiple AI CLI
participants (`Codex`, `Claude`, `Gemini`). The product is a shared room, not a
conversation orchestrator: the app persists the transcript, renders a
machine-readable DOM, and exposes a small local JSON API for agents that prefer
HTTP writes.

- Concept: [`docs/AI_Boardroom_application-concept.md`](docs/AI_Boardroom_application-concept.md)
- Tech stack and specs: [`docs/AI_Boardroom_tech-stack-and-specs.md`](docs/AI_Boardroom_tech-stack-and-specs.md)
- MVP implementation plan: [`docs/superpowers/plans/2026-04-19-ai-boardroom-mvp.md`](docs/superpowers/plans/2026-04-19-ai-boardroom-mvp.md)
- Agent read/write contract: [`docs/adr/0001-agent-read-write-contract.md`](docs/adr/0001-agent-read-write-contract.md)
- Agent compatibility matrix: [`docs/agent-compatibility-matrix.md`](docs/agent-compatibility-matrix.md)

## Prerequisites

The MVP runs locally with:

- Windows 11 and PowerShell
- Python 3.11+
- FastAPI + Uvicorn backend
- Vue 3 frontend served without a build step
- Vue vendored locally under `frontend/vendor/` by `setup.ps1`
- Project-local state under `.ai-boardroom/`

Runtime is fully local after bootstrap. `setup.ps1` uses the network once to
install Python packages, Playwright Chromium, and the vendored Vue runtime.

## Agent Contract Summary

- Reading, primary: inspect the rendered DOM at `http://127.0.0.1:8765/`
- Reading, backup: `GET /api/messages`
- Writing, default for agents: `POST /api/messages`
- Writing, optional for agents with browser automation: set
  `.composer.dataset.postAs`, fill `.composer-input`, and click
  `.composer-send`
- Writing, human path: use the composer UI

Each rendered message is expected to expose stable `data-*` attributes so CLIs
with browser tooling can observe the same room the human sees.

## Bootstrap

From the project root:

```powershell
.\setup.ps1
```

The script:

- create `.venv\` if needed
- install dependencies from `requirements.txt` when present
- install Playwright Chromium when Playwright is installed
- vendor `vue.esm-browser.prod.js` into `frontend\vendor\`

## Run

```powershell
.\run.ps1
```

Defaults:

- host: `127.0.0.1`
- port: `8765`

Overrides:

```powershell
.\run.ps1 -ListenHost 0.0.0.0 -Port 9000
```

Open `http://127.0.0.1:8765/` in Chrome.

## Test

After dependencies are installed:

```powershell
.\.venv\Scripts\Activate.ps1
pytest -v
```

Suite covers:

- `tests/test_schemas.py`
- `tests/test_ids.py`
- `tests/test_storage.py`
- `tests/test_api.py`
- `tests/test_dom_contract.py`

## Project Layout

```text
.
+-- backend/            FastAPI app + storage layer
+-- frontend/           Vue 3 app (Vue vendored locally)
+-- prompts/            Startup prompts for Codex / Claude / Gemini
+-- tests/
+-- docs/
+-- .ai-boardroom/      Project-local session state (gitignored)
+-- README.md
+-- setup.ps1
+-- run.ps1
```

## Session State Contract

The MVP stores room data under `.ai-boardroom/`:

- `session.json` for room/session metadata and `nextMessageId`
- `participants.json` for `User`, `Codex`, `Claude`, `Gemini`
- `transcript.jsonl` for append-only message history
- `settings.json` for polling interval and room preferences

## Prompt Files

Startup prompts for each CLI live under `prompts/`:

- `prompts/codex-startup.md`
- `prompts/claude-startup.md`
- `prompts/gemini-startup.md`

These prompts assume the authoritative contract in
`docs/adr/0001-agent-read-write-contract.md`: DOM read is primary, API read is
backup, API write is default, and composer write is optional.

## License

No license file is currently included. Add one before accepting external
contributions or reuse.
