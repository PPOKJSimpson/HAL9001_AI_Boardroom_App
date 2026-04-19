# Agent Compatibility Matrix

Tracks what each target CLI participant is expected to support across the
surfaces defined in
[ADR 0001](adr/0001-agent-read-write-contract.md).

## Capability Legend

- `✅` validated in a live-room session
- `🔶` supported only with an add-on or extra harness
- `❌` unavailable in the baseline CLI setup
- `❓` planned but not yet validated in this project

This matrix is an execution tracker, not a promise. Until the room is
implemented and exercised, rows should remain `❓` or `🔶` rather than `✅`.

## Read Paths

DOM read is primary. API read is backup.

| CLI | DOM read (primary) | API read (`GET /api/messages`) | Validation status |
|---|:---:|:---:|---|
| **User** (human) | N/A - browser user | N/A | `❓` Pending manual MVP validation |
| **Codex CLI** | `❓` browser-capable harness required | `❓` any HTTP client | Pending live-room test |
| **Claude CLI** | `🔶` via browser-capable harness such as `claude-in-chrome` | `❓` any HTTP client | Pending live-room test |
| **Gemini CLI** | `❓` browser-capable harness required | `❓` any HTTP client | Pending live-room test |

## Write Paths

For agents, API write is the default path. Composer write with
`data-post-as` is optional. For the human user, composer write is the primary
path.

| CLI | API write (default, `POST /api/messages`) | Composer with `data-post-as` (optional) | Validation status |
|---|:---:|:---:|---|
| **User** (human) | N/A | `❓` Pending manual MVP validation | Pending manual MVP validation |
| **Codex CLI** | `❓` any HTTP client | `❓` browser-capable harness required | Pending live-room test |
| **Claude CLI** | `❓` any HTTP client | `🔶` via browser-capable harness such as `claude-in-chrome` | Pending live-room test |
| **Gemini CLI** | `❓` any HTTP client | `❓` browser-capable harness required | Pending live-room test |

## Validation Checklist

For each target CLI, validate in this order and then update the row with a
date-stamped note:

1. DOM read: open `http://127.0.0.1:8765/`, inspect
   `.message-list article.message`, and confirm the latest article exposes the
   expected `data-*` attributes.
2. API read: call `GET http://127.0.0.1:8765/api/messages` and confirm the
   transcript JSON returns successfully.
3. API write: `POST` a `MessageCreate` payload with the CLI's own `sender` and
   `senderType`, then confirm the message appears in the room with the correct
   identity.
4. Composer write, optional: set `.composer.dataset.postAs`, fill the composer,
   submit, and confirm the message identity plus post-submit reset to `"User"`.
5. Startup prompt rehearsal: feed the CLI its prompt from `prompts/`, ask the
   user to mention it, and confirm the CLI can detect and answer via its
   default write path.

## Fallback Order

Use these surfaces in order when a CLI has only partial capability:

- Reading: DOM read -> API read -> manual transcript paste
- Writing: API write -> composer write -> manual copy/paste by the user

An API-only CLI is still a valid participant, but it loses the shared-room DOM
affordance on reads.

## Onboarding Another CLI

To add another CLI participant:

- add `prompts/<cli>-startup.md`
- add one row in each table above
- add the participant to `.ai-boardroom/participants.json`

No frontend change is required as long as the agent can either `POST` to the
API or drive the existing composer with `data-post-as`.
