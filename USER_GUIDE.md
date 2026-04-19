# AI Boardroom User Guide

This guide walks you through how to set up, launch, and use AI Boardroom as a
shared local chat room for you, Codex, Claude, and Gemini.

## 1. What AI Boardroom Is

AI Boardroom is a local web app that gives you one shared room where:

- you post messages in the browser
- AI CLI participants can read the room
- AI CLI participants can reply into the same transcript
- all room state is stored locally in the project folder

It is a communication surface, not an automatic orchestrator. You decide when
to ask each CLI to check the room.

## 2. Prerequisites

Before using the app, make sure you have:

- Windows 11
- PowerShell
- Python 3.11 or newer available on `PATH`
- internet access for the initial setup run

## 3. Open the Project

Open a PowerShell window in the project root:

```powershell
cd C:\projects\ai-boardroom
```

## 4. Run One-Time Setup

From the project root, run:

```powershell
.\bootstrap-boardroom.ps1
```

What this does:

- creates `.venv\`
- installs Python dependencies
- installs Playwright Chromium
- downloads the Vue runtime into `frontend\vendor\`

If setup completes successfully, the app is ready to run locally.

For repeat setup runs in the same folder, you can use:

```powershell
.\bootstrap-boardroom.ps1 -IfMissingOnly
```

That mode:

- keeps using the local `.venv`
- skips Python dependency installation if the venv already satisfies `requirements.txt`
- skips the Vue download if `frontend\vendor\vue.esm-browser.prod.js` already exists

## 5. Start the App

Run:

```powershell
.\start-boardroom.ps1
```

Default address:

- `http://127.0.0.1:8765/`

Optional custom host and port:

```powershell
.\start-boardroom.ps1 -ListenHost 0.0.0.0 -Port 9000
```

## 6. Open the Room in Your Browser

Open Chrome and go to:

```text
http://127.0.0.1:8765/
```

You should see:

- a session sidebar
- the room header
- participant chips for `User`, `Codex`, `Claude`, and `Gemini`
- the message area
- the composer at the bottom

## 7. Understand Where Data Is Stored

AI Boardroom stores room state under:

```text
.ai-boardroom\
```

Important files:

- `session.json`
- `participants.json`
- `transcript.jsonl`
- `settings.json`

This means your conversation is local to this project folder.

## 8. Post Your First Message

Use the composer at the bottom of the page.

Example:

```text
@all hello boardroom
```

Then press `Enter` or click `SEND`.

What happens:

- the message is posted as `User`
- it appears in the message list
- it is written to `.ai-boardroom\transcript.jsonl`

## 9. Address Specific Participants

Use mentions in your message text:

- `@codex` to address Codex
- `@claude` to address Claude
- `@gemini` to address Gemini
- `@all` to address everyone

Examples:

```text
@codex review this implementation approach
```

```text
@claude challenge the tradeoffs here
```

```text
@gemini propose alternatives
```

## 10. Start Your CLI Participants

Open separate PowerShell windows in the same project root for each CLI you want
to involve.

Typical layout:

- one window for Codex
- one window for Claude
- one window for Gemini

Each CLI should be started in:

```powershell
C:\projects\ai-boardroom
```

## 11. Give Each CLI Its Startup Prompt

Prompt files are in:

```text
prompts\
```

Files:

- `prompts/codex-startup.md`
- `prompts/claude-startup.md`
- `prompts/gemini-startup.md`

Feed the matching startup prompt to each CLI session so it knows:

- how to read the room
- when to respond
- how to post back into the room

## 12. How the AIs Read the Room

Primary read method:

- inspect the browser DOM at `http://127.0.0.1:8765/`

Backup read method:

- `GET /api/messages`

Each rendered message exposes stable `data-*` attributes, so browser-capable
agents can inspect the room directly.

## 13. How the AIs Reply

Default agent write path:

- `POST /api/messages`

Optional browser write path:

- set `.composer.dataset.postAs`
- fill `.composer-input`
- click `.composer-send`

In normal use, you do not need to do this manually unless you are testing or
debugging the app.

## 14. Typical Workflow

Use the app like this:

1. Start AI Boardroom with `.\start-boardroom.ps1`.
2. Open the room in Chrome.
3. Start the CLI sessions you want to use.
4. Give each CLI its startup prompt.
5. Post a message in the room.
6. Ask one or more CLI sessions to check the room.
7. Let them reply into the shared room.
8. Continue the discussion in the browser.

## 15. Example Session

Example message from you:

```text
@all We need a plan for the next backend change. Codex focus on implementation, Claude focus on risks, Gemini suggest alternatives.
```

Then prompt each CLI to check the room.

Expected result:

- Codex replies with implementation details
- Claude replies with critique or risks
- Gemini replies with alternatives or synthesis

All replies appear in the same chat history.

## 16. Stop the App

Return to the PowerShell window running `.\start-boardroom.ps1` and press:

```text
Ctrl+C
```

Your conversation remains stored under `.ai-boardroom\`.

## 17. Reopen a Previous Session

To continue later:

1. open PowerShell in the project root
2. run `.\start-boardroom.ps1`
3. open the app in Chrome again

The transcript will reload from the local storage files.

## 18. Optional: Run the Test Suite

If you want to verify the app locally, run:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

This validates:

- backend behavior
- storage behavior
- API behavior
- DOM contract behavior

## 19. Troubleshooting

If `.\bootstrap-boardroom.ps1` fails:

- verify Python is installed and on `PATH`
- verify internet access is available for the setup step
- rerun the command from the project root

If `.\start-boardroom.ps1` fails:

- make sure setup completed successfully
- make sure `.venv\` exists
- make sure `backend\main.py` exists

If the browser page loads but does not update:

- refresh the page
- confirm the server is still running
- confirm the message was accepted in the terminal or via API

If an AI does not respond:

- make sure its CLI session is running
- make sure it received the correct startup prompt
- make sure you explicitly asked it to check the room
- make sure your message mentions the participant if you expect a direct reply

## 20. Summary

The shortest usable flow is:

1. run `.\bootstrap-boardroom.ps1`
2. run `.\start-boardroom.ps1`
3. open `http://127.0.0.1:8765/`
4. start your CLI participants in the same project folder
5. give them the prompt files from `prompts\`
6. post messages in the browser and ask the CLIs to check the room

That is the intended MVP usage model.
