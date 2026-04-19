# ADR 0002 — Session Model

- **Status:** Accepted
- **Date:** 2026-04-19
- **Related:** [ADR 0001 — Agent read/write contract](./0001-agent-read-write-contract.md), [AI Boardroom application concept](../AI_Boardroom_application-concept.md), [AI Boardroom tech stack and specs](../AI_Boardroom_tech-stack-and-specs.md)

## Context

The original MVP documentation assumed a single flat session layout under
`.ai-boardroom/`: one `session.json` and one `transcript.jsonl` at the project
root. That was enough to validate the shared-room concept, but it creates two
problems once the product moves from a one-off demo toward repeated use.

First, a permanent single session makes launches feel sticky. If the user opens
AI Boardroom for a new task, they inherit whatever transcript happened to be
there last time. That raises the cognitive load for both the user and the AI
participants, because they need to distinguish "today's room" from older
history that happens to live in the same transcript.

Second, preserving only one session throws away useful project context. Past
discussions, architecture reviews, and implementation threads are still
valuable, but they should be preserved as prior sessions rather than blended
into the currently active room.

A fully parallel multi-active session model was considered and rejected for the
current phase. It would introduce concurrent-room UX, routing, and state
consistency concerns that are out of proportion to the MVP's goals. The product
still wants one active room at a time, not a dashboard of simultaneously live
rooms.

The design goal is therefore:

- Keep the simple mental model of one current session
- Start fresh by default on each explicit user launch
- Preserve prior sessions on disk so the user can reactivate them later
- Keep agent I/O semantics unchanged from ADR 0001

## Decision

### Session shape

AI Boardroom uses a **single-active-session model with preserved prior
sessions**. Only one session is current at any moment, but previous sessions
remain on disk and can be listed and reactivated.

Each session gets its own self-contained folder:

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

- `current-session.json` is a pointer file containing the current session id.
- `participants.json` and `settings.json` remain global to the project.
- `sessions/<id>/session.json` stores per-session metadata such as title,
  timestamps, room name, and `nextMessageId`.
- `sessions/<id>/transcript.jsonl` stores only that session's transcript.

### Startup behavior

Startup creates or resumes the current session through the pointer file, not by
reading a root-level transcript.

- `init_storage()` ensures the directory structure exists and performs any
  one-time migration from the legacy flat layout.
- `ensure_current_session()` creates a new session when the pointer is missing
  or stale, and returns the pointed-at session when it is valid.
- The launcher deletes `current-session.json` before a normal user launch, so a
  new launch starts a fresh empty session by default.
- A resume-style launch may preserve the pointer to keep working in the same
  session.

This gives the user a clean room per launch without discarding prior work.

### API surface

The existing message/session endpoints continue to operate on the current
session:

- `GET /api/session`
- `GET /api/messages`
- `POST /api/messages`

The backend also exposes explicit session-management endpoints:

- `GET /api/sessions` to list saved sessions
- `POST /api/sessions` to create a new session and make it current
- `POST /api/sessions/{id}/activate` to switch the current session
- `PATCH /api/sessions/{id}` to rename a session

This keeps the room model simple in the frontend: there is still one active
room, but the user can switch which preserved session that room represents.

### Migration

Legacy projects that still have `.ai-boardroom/session.json` and
`.ai-boardroom/transcript.jsonl` at the root are migrated once into
`sessions/<id>/`, and the pointer file is written to that migrated session.

## Consequences

### Positive

- Every explicit user launch starts in a clean session by default.
- Previous sessions remain available for later review or reactivation.
- Session history stays scoped cleanly on disk instead of being merged into one
  ever-growing transcript.
- The one-active-room mental model remains intact for the UI and for AI
  participants.

### Negative

- Disk usage grows with the number of sessions. This is accepted for MVP
  because the storage format is transparent, local, and easy to inspect.
- Session cleanup is manual until a dedicated cleanup/delete UI exists.
- Migration is one-way at the storage-layout level once legacy root files are
  moved into `sessions/<id>/`.

### Neutral

- There is no cross-session mutation or shared transcript editing; each write
  targets only the current session.
- ADR 0001 remains unchanged. The DOM is still the primary read surface, and
  agent write behavior does not depend on the session layout.

## Future Reconsideration

Revisit this decision if:

- Users need multiple concurrently active sessions or rooms at the same time
- AI Boardroom moves beyond a local single-user deployment
- We add remote collaboration or multi-user semantics
- We ship a first-class session cleanup, archival, or retention-management UI

Any of those would justify a new ADR rather than silently stretching the
current single-active-session model beyond its intended scope.
