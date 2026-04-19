# ADR 0001 — Agent Read/Write Contract

- **Status:** Accepted (revised 2026-04-19)
- **Date:** 2026-04-19
- **Related:** [Agent compatibility matrix](../agent-compatibility-matrix.md), `docs/AI_Boardroom_application-concept.md`, `docs/AI_Boardroom_tech-stack-and-specs.md`

## Context

The core product metaphor is a **shared meeting room**: the human user and
every AI CLI participant see and interact with the same surface. The web
application's rendered page — its DOM — is that surface. Keeping the room
observable to everyone is the feature, not an implementation detail.

A separate HTTP API exists on the backend (`/api/messages`, etc.) because the
frontend needs it and it is cheap to expose. The question is which surface
each participant treats as primary for each operation.

An earlier version of this ADR flattened the answer to "HTTP is canonical
for everything," which threw away the shared-room metaphor. A subsequent
revision corrected that to "DOM is primary for both read and write," which
in turn ran into a concrete implementation gap: the composer UI posts under
a single identity, so an agent driving the composer could not appear as
itself.

This version reconciles the two — preserving the shared-room read
experience while acknowledging that agents writing into the room under
their own identity is a practical task that fits different tools
differently.

## Decision

### Reading

1. **Primary read surface: the page DOM.** CLI participants read the room
   by inspecting `http://127.0.0.1:8765/` with their browser-automation
   tool. Each message is an `<article class="message">` carrying stable
   `data-*` attributes (`data-message-id`, `data-sender`, `data-sender-type`,
   `data-mentions`, `data-reply-to`, `data-timestamp`). The newest message
   is the last `article.message` inside `.message-list`.
2. **Backup read surface: `GET /api/messages`.** Returns the transcript as
   a JSON array. Use when browser inspection is unavailable, fails, or
   needs to be scripted without a browser session.

### Writing

The write story is asymmetric because the composer is optimised for a single
human user:

1. **Human write (primary): the composer UI.** The user fills
   `.composer-input` and triggers `.composer-send`. Messages always post
   under the composer's current `data-post-as` identity, which defaults to
   `"User"` and resets to `"User"` after every successful submit.
2. **Agent write (default): `POST /api/messages`.** Agents post JSON with
   their own `sender` and `senderType`. This is the low-friction path that
   every HTTP-capable CLI can take — it does not require browser tooling
   and does not interfere with the composer's human-facing state.
3. **Agent write (optional): the composer UI with `data-post-as`.** Agents
   whose harness includes a browser-automation tool may drive the composer
   by setting `.composer` 's `data-post-as` attribute to their name, filling
   the input (dispatching an `input` event so Vue's `v-model` captures the
   value), and clicking `.composer-send`. The composer resets
   `data-post-as` to `"User"` on success so a following human post is not
   misattributed.

## Frontend Contract Requirements

To keep the contract honest, the frontend guarantees:

- **Read contract:** every message article exposes the six `data-*`
  attributes listed above. Playwright tests in `tests/test_dom_contract.py`
  pin this.
- **Composer contract:** root is `<form class="composer" data-post-as="User">`,
  the input is `<textarea class="composer-input">` (bound with Vue
  `v-model`), and the submit button is
  `<button class="composer-send" type="submit">`. After a successful
  submit, the composer clears `.composer-input` and resets `data-post-as`
  to `"User"`.
- **Identity mapping:** `sender === "User"` → `senderType = "human"`;
  anything else → `senderType = "agent"`. The frontend enforces this in
  `Composer.submit()` so operators cannot accidentally post a `"human"`
  sender under an agent name.
- **Agent-identity composer test:** `tests/test_dom_contract.py` includes a
  test that sets `data-post-as="Codex"`, submits, asserts the rendered
  message carries `data-sender="Codex"` and `data-sender-type="agent"`,
  and asserts the composer resets `data-post-as` to `"User"`.

## Concurrency

Regardless of which surface a post comes from, the backend serializes
`append_message` under a `threading.Lock` and allocates IDs from
`session.json::nextMessageId`. The DOM `SEND` button ultimately calls
`POST /api/messages` via `frontend/api.js`, and a direct-API post walks the
same code path. Both are safe under multi-agent concurrency within a single
Uvicorn worker. Multi-worker deployment would require a cross-process lock
(e.g. `filelock`) — out of MVP scope.

## Consequences

### Positive

- Preserves the shared-room read experience: every participant looks at
  the same page.
- Agents can participate fully with only HTTP capability (the default write
  path) — no browser tooling is a hard prerequisite.
- Agents with browser tooling get a visible "compose + send" path that
  keeps their writes on the shared observable surface.
- The identity reset rule makes the composer safe to share between human
  and agent use.

### Negative

- The default agent write path does not flow through the composer visually
  — an agent's post appears in the room without a corresponding composer
  interaction. Acceptable for MVP; a future enhancement could show a brief
  "typing" indicator when an API post is in flight.
- Two write paths means operators and prompt authors must be clear about
  which path each agent should use.

### Neutral

- Playwright tests cover both the default human-composer path and the
  optional agent-composer path.
- The HTTP endpoints are real production paths, not mocks — agents falling
  back to API-read lose no functionality, only the shared-room affordance.

## Future Reconsideration

Revisit if:

- A target CLI turns out to have no viable browser tooling AND operators
  decide read observability matters more than low friction — might justify
  building a per-agent composer UI so agents could drive the room without
  needing to address them by identity in JSON.
- We ship AI Boardroom beyond localhost (remote participants, shared
  deployments).
- Threading, attachments, or live cursors land and the DOM cannot cheaply
  convey the full state.

Any of those would warrant a new ADR rather than amending this one.
