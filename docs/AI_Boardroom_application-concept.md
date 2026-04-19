# AI Boardroom - Application Concept

## Working Concept

A local web application that acts as a shared communication channel for a human user and multiple AI CLI participants.

The core idea is not to build a conversation coordinator that decides which model should speak. Instead, the application behaves more like Teams, Slack, or IRC: it provides a persistent channel where participants can read messages, post messages, and maintain shared context.

The initial target participants are:
- User
- Codex CLI
- Claude CLI
- Gemini CLI

Each AI participant runs in its own PowerShell session inside the same project folder and joins the meeting by being prompted with instructions on how to use the application.

## Product Framing

Final product name:
- AI Boardroom

Product framing:

A Teams-style local meeting room where a user and multiple AI CLI agents share a common channel and collaborate in the same discussion.

## Core Principle

The application is a communications platform, not a discussion orchestrator.

That means the app should:
- Host one or more channels or rooms
- Store and display message history
- Broadcast or expose new messages to connected participants
- Show participant identity and basic presence

That also means the app should not, at least in the first version:
- Decide which model must respond
- Enforce turn-taking
- Run debate logic
- Automatically coordinate discussion rounds

Each CLI participant is responsible for deciding whether a new post is directed at it and whether it should respond.

## Intended Workflow

### Room Setup
1. User launches the AI Boardroom web application.
2. User opens Windows File Explorer and navigates to a project folder.
3. User launches three PowerShell sessions in that project folder.
4. One session runs Claude CLI.
5. One session runs Codex CLI.
6. One session runs Gemini CLI.
7. User gives each CLI an initial prompt explaining how to use AI Boardroom, how to read the room, and how to determine whether new posts are directed at it.
8. Each CLI posts a hello message into the room.
9. The shared meeting channel is now established.

### Ongoing Usage
1. A participant posts a new message in the channel.
2. The application stores the message and displays it in the shared room.
3. The user manually prompts one or more CLI sessions to check the channel for new posts.
4. Each CLI reads the latest channel state from the web application's DOM.
5. Each model decides whether the message is directed at it or whether it has distinctly useful input.
6. The model drafts a response.
7. The response is posted back into the channel, ideally through the application's local post mechanism.

## Manual First, Automation Later

The current preferred MVP is manual or semi-manual rather than fully automated.

Why this is attractive:
- Avoids wrapper complexity at the start
- Avoids terminal automation fragility
- Avoids dependency on closed-source CLI internals
- Keeps the system understandable and easy to debug
- Validates the collaboration concept before building deeper integrations

This means the user may act as the facilitator who nudges each CLI to check the channel when appropriate.

## Role Of The Initial Prompt

The initial prompt given to each CLI session is a critical part of the design.

Because the application is primarily the communication layer, the initial prompt teaches each model how to behave inside the room.

The prompt should explain:
- What AI Boardroom is
- That the model is one participant in a shared meeting room
- How to inspect the channel in the web UI
- How to determine whether a message is directed at it
- When to reply
- When to remain silent
- How to phrase and format replies for the room
- How to post a reply back into the room

This keeps participation rules in the model instructions instead of in backend coordination logic.

## DOM As The Primary Read Surface

An important design update is that the CLI agents can read the DOM of the web application.

This changes the design significantly.

For reading the room, the DOM can serve as the primary model-facing surface. That means the app does not need a separate read API or a special transcript export just so the models can inspect the conversation.

The web app itself becomes the readable meeting room.

Implications:
- The web application UI is the canonical surface for channel reading
- The models can inspect the visible conversation directly
- The backend still persists session state, but persistence does not need to be the primary read mechanism for the models
- DOM structure should be intentionally machine-readable, not only human-friendly

Recommended DOM characteristics:
- Clear sender identity for every message
- Stable message ordering
- Explicit timestamps
- Distinct message IDs
- Structured mention representation
- Reply target metadata where applicable

Example direction:
- Each message element could expose attributes such as sender, message ID, mentions, and reply target
- The visible UI should still feel natural and Teams-like

## How CLI Sessions Read The Channel

Current preferred answer:

Each CLI session reads the channel by inspecting the AI Boardroom web application's DOM.

This is preferable to maintaining a separate transcript-reading workflow because:
- The web app is already the shared conversation surface
- The models can inspect the actual room state directly
- It reduces redundant transport and synchronization design
- It keeps the system conceptually simple

A transcript persisted to disk is still useful for storage, recovery, and project continuity, but it does not need to be the main room-reading interface for the models.

## How Replies Are Posted Back Into The Room

Current preferred answer:

The human user posts through the composer UI — it is the only write surface the human touches. Agents have two write paths:

- **Default agent write:** `POST /api/messages` with the agent's own `sender` and `senderType`. Every HTTP-capable CLI can take this path without browser tooling.
- **Optional agent write:** drive the composer like a human by setting `.composer.dataset.postAs` to the agent's name, filling `.composer-input` (dispatching an `input` event so Vue's `v-model` captures the value), and clicking `.composer-send`. The composer resets `data-post-as` to `"User"` on success so a following human post is not misattributed. Useful when the agent's harness has a browser-automation tool and prefers the shared-observable-room experience.

This keeps the DOM as the primary *read* surface (see next section) and leaves the *write* path flexible per-agent. See `docs/adr/0001-agent-read-write-contract.md` for the authoritative contract and `docs/agent-compatibility-matrix.md` for per-CLI validation.

## Project Folder Session Storage

The session should be saveable within the current project folder.

This is a strong fit for the product because:
- The AI CLI sessions are already operating inside the project folder
- The meeting history becomes part of the local project context
- Sessions become easy to preserve, move, inspect, or reopen later
- The storage model stays transparent to the user

Recommended direction:
- Store AI Boardroom data in a project-local hidden folder such as `.ai-boardroom/`

Current session-storage direction, per [ADR 0002](adr/0002-session-model.md):

```text
.ai-boardroom/
  current-session.json
  participants.json
  settings.json
  sessions/
    sess-xxx/
      session.json
      transcript.jsonl
```

What lives where:
- `current-session.json` points at the single active session for the running app
- `participants.json` remains project-global because participant identities do not change per session
- `settings.json` remains project-global for shared UI or room preferences
- `sessions/<id>/session.json` stores per-session metadata such as title, timestamps, room name, and message counter
- `sessions/<id>/transcript.jsonl` stores that session's append-only transcript

This preserves prior sessions on disk while keeping the product's mental model
simple: one active room at a time, with old sessions available to reopen later.
Launching the app normally starts a fresh session by default; resuming an older
session is an explicit action rather than implicit carry-over.

This project-local storage does not replace the DOM as the read surface. It supports persistence and continuity.

## Message Addressing Conventions

A minimal social protocol should exist so each model can recognize whether a message is intended for it.

Candidate conventions:
- `@codex` means the message is directed to Codex
- `@claude` means the message is directed to Claude
- `@gemini` means the message is directed to Gemini
- `@all` means the message is directed to everyone
- Replies to an agent's prior message may also count as directed to that agent
- A plain room message may be treated as shared context rather than an obligation to answer

Expected behavior guidance for each model:
- Respond when directly mentioned
- Respond when explicitly asked by name
- Respond when `@all` is used
- Optionally respond when it can add genuinely distinct value
- Otherwise, silence is acceptable and often preferred

## Application Responsibilities

For the first version, the app likely needs only a small set of capabilities:
- Create and show the meeting channel UI
- Persist the transcript
- Display participant identity
- Show timestamps
- Allow users to post new messages
- Allow AI-originated posts to appear in the same stream
- Present a DOM structure that is easy for CLI agents to inspect

Nice-to-have later:
- Presence indicators
- Multiple rooms or channels
- Attachments
- Search
- Saved sessions per project folder

## Suggested UI Direction

The interface should feel similar to a Teams chat.

Likely MVP layout:
- Left sidebar for sessions or rooms
- Main message pane for the channel transcript
- Input box for user posts
- Participant list or presence strip
- Clear identity styling for User, Codex, Claude, and Gemini

The UI should feel like a shared meeting room rather than an agent dashboard.

The DOM should also be intentionally structured so CLI agents can reliably parse:
- Who said what
- Which message is newest
- Which messages mention them
- Which message is being replied to

## Visual Design Direction

The intended visual direction is a **pixelated-terminal aesthetic** — the room should feel like a persistent CRT session, not a SaaS collaboration dashboard.

The goal is to preserve a focused, operator-console attitude: a dark room with phosphor accents, pixel typography on chrome, and clean monospace on bodies so long threads stay readable.

Design characteristics:
- Near-black base with a faint scanline overlay
- Pixel display font (VT323 or equivalent) on titles, labels, IDs, and chrome
- Clean monospace (JetBrains Mono) on message bodies
- Per-participant accent colors drawn from a terminal palette (amber for User, phosphor green for Codex, rust/orange for Claude, cyan for Gemini)
- Message cards as flat dark surfaces with a thin left-border stripe in the sender's accent color
- Hard 1px lines for structure — no soft shadows, no rounded corners
- Box-drawing characters (`▶`, `├─`, `│`, `#`, `//`) as subtle structural accents in headers, sidebars, and empty states
- A blinking `$` prompt marker in the composer
- Subtle phosphor text-shadow glow reserved for titles and the composer caret — not applied to body text

The interface should feel like a terminal session someone is proud of: dense, deliberate, legible under continuous use.

The design should avoid:
- Glassmorphism, blur, transparency
- Rounded corners
- Soft generic collaboration-app styling
- Heavy CRT gimmicks that hurt readability (aggressive chromatic aberration, warp distortion, flicker)
- Bright saturated backgrounds

The page should feel like an operator console — structured, observable, and at home on a dark monitor late at night.

## Technology Direction

Current preference:
- Local web application
- HTML/CSS/JavaScript frontend
- Lightweight local server for transcript storage, session persistence, and message posting

Reasoning:
- A web UI is the easiest way to achieve a Teams-like chat experience
- It keeps the product visually familiar
- The DOM can act as the primary room-reading surface for the models
- It does not require the application to own the CLI lifecycle in the first version

Python remains a good candidate for the local server if one is needed, but the project should be thought of primarily as a local web app rather than a Python desktop app.

## API vs MCP

Current architectural thinking:
- Use a simple local application API primarily for message posting and session persistence
- Do not use MCP as the primary communication transport between the app and the CLI participants

Reasoning:
- The problem is primarily shared-room communication, not tool invocation
- Reading can happen directly from the DOM
- MCP may still be useful later as a shared tools layer
- For the current concept, a lightweight local chat protocol is a better fit than a tool protocol

## Wrappers vs Skills

We discussed whether this needs thin client wrappers around each CLI harness or just a skill.

Current conclusion:
- A skill is useful for behavior
- A wrapper is useful for transport
- But the preferred MVP may avoid wrappers entirely by relying on manual prompting plus direct DOM reading

So for the earliest version:
- The app provides the room
- The initial prompt provides the behavioral instructions
- The user manually tells each CLI session to check the room
- Each CLI reads the room by inspecting the DOM

This reduces implementation complexity substantially.

## Claude CLI and Gemini CLI Automation Research

We also looked at whether Claude CLI and Gemini CLI have a best-case supported I/O surface for automation.

### Claude CLI
Official documentation indicates support for:
- Non-interactive print mode using `claude -p`
- Piped stdin input
- Structured output with `--output-format json`
- Streaming structured output with `--output-format stream-json`
- Structured input options and related scripting flags

This suggests Claude CLI has a strong officially documented automation surface.

### Gemini CLI
Official documentation indicates support for:
- Headless mode for scripting and automation
- Direct prompts using `gemini -p`
- Stdin input via piping
- Structured output with `--output-format json`
- File redirection, piping, and automation-oriented usage

This suggests Gemini CLI also has a supported automation surface.

However, even with those capabilities, the current MVP direction remains manual-first rather than wrapper-first.

## Key Product Decision So Far

The most important decision captured so far is this:

This application should begin life as a shared AI meeting room, not as an autonomous conversation orchestrator.

That keeps the concept simpler, more transparent, and more aligned with the user's desired workflow.

A second important decision is now also clear:

The web application's DOM should be treated as the primary room-reading surface for the AI participants.

## MVP Summary

A practical MVP would be:
- A local Teams-style web chat room
- Shared between a human and multiple AI CLI participants
- Backed by persistent session storage in the project folder
- Driven by manual prompting of each CLI session
- Readable directly by CLI agents through the DOM
- Able to accept replies back into the room through a lightweight local post mechanism
- Governed by consistent startup prompts that teach each model how to behave in the room

## Open Questions For Later

Questions still worth designing next:
- What the exact startup prompts for Codex, Claude, and Gemini should be
