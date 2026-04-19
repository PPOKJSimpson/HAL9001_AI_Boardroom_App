# Terminal UI Update — Implementation Plan

> **Scope:** Replace the current neo-brutalist stylesheet with a pixelated-terminal aesthetic across the already-built frontend. Backend, components, tests, and storage layer are unchanged.

**Goal:** Swap `frontend/styles/brutalist.css` for a new `frontend/styles/terminal.css` (dark phosphor palette, VT323 + JetBrains Mono fonts, per-participant accent colors, blinking `$` composer prompt, subtle scanline overlay) and ship the required font files directly in the repo.

**Reference preview:** `docs/terminal-preview.html` — opened in Chrome, this is the look we're targeting. Use it as the visual acceptance bar. Before using it as the reference, scrub any machine-local example path from the sidebar so the preview stays publication-safe.

**Out of scope:**
- Any backend, component, or test logic changes
- HTML structure changes in components (the CSS works against the existing DOM contract)
- Cleanup of stray `pytest-cache-files-*` directories at the repo root (separate concern)

---

## Current State Snapshot

Verified at authoring time on 2026-04-19:

- `frontend/index.html` links `/styles/brutalist.css`
- `frontend/styles/` contains only `brutalist.css` — no `terminal.css` yet
- `frontend/vendor/` contains `vue.esm-browser.prod.js` — no `fonts/` subdirectory yet
- `bootstrap-boardroom.ps1` vendors Vue but does not need to vendor fonts for this update
- `frontend/app.js`, all components under `frontend/components/`, and `frontend/api.js` are already in place and correct — no changes needed there

---

## File Changes At A Glance

| Action | Path |
|---|---|
| Modify | `.gitignore` — allow committed font assets under `frontend/vendor/fonts/` while still ignoring the vendored Vue runtime |
| Add | `frontend/vendor/fonts/VT323-Regular.woff2` |
| Add | `frontend/vendor/fonts/JetBrainsMono-Regular.woff2` |
| Add | `frontend/vendor/fonts/JetBrainsMono-Bold.woff2` |
| Add | `frontend/styles/terminal.css` |
| Modify | `frontend/index.html` — change stylesheet link from `brutalist.css` to `terminal.css` |
| Delete | `frontend/styles/brutalist.css` — only after visual verification passes |

---

## Task 1: Allow committed fonts under `frontend/vendor/fonts/`

**File:** `.gitignore`

The repo currently ignores `frontend/vendor/` wholesale. That must be narrowed before committed font assets can be staged.

- [ ] **Step 1:** Replace the broad `frontend/vendor/` ignore rule with a narrower rule set that still ignores the vendored Vue runtime but allows committed fonts:

```gitignore
frontend/vendor/*
!frontend/vendor/fonts/
!frontend/vendor/fonts/**
frontend/vendor/vue.esm-browser.prod.js
```

- [ ] **Step 2:** Verify the new rule shape:

```powershell
Get-Content .\.gitignore
git check-ignore -v .\frontend\vendor\vue.esm-browser.prod.js
git check-ignore -v .\frontend\vendor\fonts\VT323-Regular.woff2
```

Expected:
- `vue.esm-browser.prod.js` is still ignored
- the font path is not ignored

- [ ] **Step 3:** Commit

```bash
git add .gitignore
git commit -m "chore(ui): allow committed font assets under frontend/vendor/fonts"
```

---

## Task 2: Commit the font files

**Files:**
- `frontend/vendor/fonts/VT323-Regular.woff2`
- `frontend/vendor/fonts/JetBrainsMono-Regular.woff2`
- `frontend/vendor/fonts/JetBrainsMono-Bold.woff2`

Add the three font files directly to the repository so the terminal theme is reproducible without network fetches from mutable third-party URLs.

- [ ] **Step 1:** Create `frontend/vendor/fonts/` if missing.

- [ ] **Step 2:** Add these three files:

- `VT323-Regular.woff2`
- `JetBrainsMono-Regular.woff2`
- `JetBrainsMono-Bold.woff2`

- [ ] **Step 3:** Verify they exist and are tracked:

```powershell
Get-ChildItem .\frontend\vendor\fonts
git status --short .\frontend\vendor\fonts
```

Expected:
- all three files exist under `frontend\vendor\fonts\`
- `git status` shows them as added or modified, not ignored

- [ ] **Step 4:** Commit

```bash
git add frontend/vendor/fonts
git commit -m "chore(ui): commit VT323 and JetBrains Mono font assets"
```

---

## Task 3: Scrub `docs/terminal-preview.html`

**File:** `docs/terminal-preview.html`

The preview is the visual acceptance reference for this update. It must not contain the old machine-local example path.

- [ ] **Step 1:** Replace the current project-path example in the sidebar with a neutral public-safe path such as:

```text
C:\projects\ai-boardroom
```

- [ ] **Step 2:** Commit

```bash
git add docs/terminal-preview.html
git commit -m "docs(ui): scrub local path from terminal preview"
```

---

## Task 4: Create `frontend/styles/terminal.css`

**File:** `frontend/styles/terminal.css`

Drop in the stylesheet below. Palette, typography, grid, scanline overlay, blinking prompt, and per-sender accent stripes are all defined here. The stylesheet works against the existing component DOM unchanged — it relies on class names and `data-*` attributes the components already emit (`.message-list`, `.composer`, `.composer-input`, `.composer-send`, `article.message`, `data-sender`, `.participant-chip`, `.participant-name-<name>`, `.room-header`, `.room-title`, `.session-sidebar`, `.sidebar-header`, `.session-facts`, `.empty-room`, `.error-banner`).

**Grid-nesting note:** the app mounts Vue into `#app`, which contains a single `.app-shell` child. The stylesheet uses `display: contents` on `#app` so the two-column grid lives on `.app-shell` directly against the viewport. Applying grid to both collapses the main column — this is a real bug found in the preview.

- [ ] **Step 1:** Create `frontend/styles/terminal.css` with this content:

```css
/* Committed font assets — stored under frontend/vendor/fonts/. */
@font-face {
  font-family: "VT323";
  src: url("/vendor/fonts/VT323-Regular.woff2") format("woff2");
  font-weight: 400;
  font-display: swap;
}
@font-face {
  font-family: "JetBrains Mono";
  src: url("/vendor/fonts/JetBrainsMono-Regular.woff2") format("woff2");
  font-weight: 400;
  font-display: swap;
}
@font-face {
  font-family: "JetBrains Mono";
  src: url("/vendor/fonts/JetBrainsMono-Bold.woff2") format("woff2");
  font-weight: 700;
  font-display: swap;
}

:root {
  --bg:          #0a0e0a;
  --bg-elev:     #10161a;
  --bg-sunk:     #05080a;
  --ink:         #cfd8d2;
  --ink-dim:     #7a8880;
  --ink-faint:   #4a5550;
  --line:        #1f2a24;
  --line-strong: #2f3d34;

  --phosphor: #33ff66;
  --amber:    #ffb000;
  --orange:   #ff7f3f;
  --cyan:     #00d4ff;
  --danger:   #ff5555;

  --sender-user:   var(--amber);
  --sender-codex:  var(--phosphor);
  --sender-claude: var(--orange);
  --sender-gemini: var(--cyan);

  --font-display: "VT323", "Courier New", monospace;
  --font-body:    "JetBrains Mono", "Cascadia Mono", Consolas, monospace;

  --glow-soft: 0 0 6px currentColor;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  height: 100%;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.5;
}

/* CRT scanline overlay. Remove this rule to turn it off. */
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.18) 0px,
    rgba(0, 0, 0, 0.18) 1px,
    transparent 1px,
    transparent 3px
  );
  z-index: 1000;
}

/* #app holds a single .app-shell. Use display:contents so .app-shell owns
   the grid against the viewport — applying grid to both collapses the
   main column into the sidebar's 280px track. */
#app { height: 100vh; display: contents; }
.app-shell {
  height: 100vh;
  display: grid;
  grid-template-columns: 280px 1fr;
}

/* Sidebar */

.session-sidebar {
  background: var(--bg-elev);
  border-right: 1px solid var(--line);
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-header {
  font-family: var(--font-display);
  font-size: 28px;
  color: var(--phosphor);
  text-shadow: var(--glow-soft);
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--line-strong);
  padding-bottom: 8px;
}
.sidebar-header::before { content: "▶ "; }

.session-facts { margin: 0; display: grid; gap: 2px; }
.session-facts dt {
  font-family: var(--font-display);
  font-size: 16px;
  color: var(--ink-dim);
  letter-spacing: 0.08em;
}
.session-facts dt::before { content: "├─ "; color: var(--ink-faint); }
.session-facts dd {
  margin: 0 0 10px 18px;
  font-family: var(--font-body);
  color: var(--ink);
  word-break: break-all;
  font-size: 12px;
}

/* Main */

.room-main {
  display: grid;
  grid-template-rows: auto 1fr auto;
  min-height: 0;
  background: var(--bg);
}

.room-header {
  border-bottom: 1px solid var(--line);
  padding: 10px 20px;
  background: var(--bg-elev);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.room-title-block { display: flex; align-items: baseline; gap: 10px; }

.room-label {
  font-family: var(--font-display);
  font-size: 16px;
  color: var(--ink-dim);
  letter-spacing: 0.15em;
}

.room-title {
  font-family: var(--font-display);
  font-size: 32px;
  color: var(--phosphor);
  text-shadow: var(--glow-soft);
  margin: 0;
  letter-spacing: 0.02em;
}
.room-title::before { content: "# "; color: var(--ink-dim); }

/* Participants */

.participant-strip {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.participant-chip {
  padding: 2px 8px;
  background: transparent;
  border: 1px solid currentColor;
  font-family: var(--font-display);
  font-size: 17px;
  display: inline-flex;
  gap: 6px;
  align-items: center;
  letter-spacing: 0.04em;
}
.participant-chip .participant-role { display: none; }

.participant-name-user   { color: var(--sender-user); }
.participant-name-codex  { color: var(--sender-codex); }
.participant-name-claude { color: var(--sender-claude); }
.participant-name-gemini { color: var(--sender-gemini); }

/* Messages */

.room-scroll {
  overflow-y: auto;
  padding: 14px 20px 20px;
  background: var(--bg);
  min-height: 0;
  scrollbar-width: thin;
  scrollbar-color: var(--line-strong) var(--bg);
}
.room-scroll::-webkit-scrollbar { width: 8px; }
.room-scroll::-webkit-scrollbar-track { background: var(--bg); }
.room-scroll::-webkit-scrollbar-thumb { background: var(--line-strong); }
.room-scroll::-webkit-scrollbar-thumb:hover { background: var(--ink-dim); }

.message-list { display: flex; flex-direction: column; gap: 8px; }

.message {
  background: var(--bg-elev);
  border-left: 2px solid var(--ink-faint);
  padding: 6px 14px 8px;
  max-width: 820px;
}

article[data-sender="User"]   { border-left-color: var(--sender-user); }
article[data-sender="Codex"]  { border-left-color: var(--sender-codex); }
article[data-sender="Claude"] { border-left-color: var(--sender-claude); }
article[data-sender="Gemini"] { border-left-color: var(--sender-gemini); }

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 2px;
  gap: 12px;
}

.sender {
  font-family: var(--font-display);
  font-size: 18px;
  letter-spacing: 0.03em;
}
.sender::before { content: "["; color: var(--ink-dim); }
.sender::after  { content: "]"; color: var(--ink-dim); }

.sender-user   { color: var(--sender-user); }
.sender-codex  { color: var(--sender-codex); }
.sender-claude { color: var(--sender-claude); }
.sender-gemini { color: var(--sender-gemini); }

time {
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--ink-faint);
}

.message-body {
  white-space: pre-wrap;
  word-wrap: break-word;
  color: var(--ink);
  font-size: 14px;
}

.empty-room {
  text-align: center;
  padding: 60px 20px;
  color: var(--ink-faint);
  font-family: var(--font-display);
  font-size: 20px;
  letter-spacing: 0.08em;
}
.empty-room::before { content: "// "; color: var(--ink-faint); }

/* Composer */

.composer {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: stretch;
  border-top: 1px solid var(--line);
  background: var(--bg-elev);
}

.composer::before {
  content: "$";
  font-family: var(--font-display);
  color: var(--phosphor);
  font-size: 22px;
  padding: 10px 0 10px 16px;
  align-self: start;
  animation: blink 1.2s steps(2) infinite;
  text-shadow: var(--glow-soft);
}

@keyframes blink {
  0%, 50%       { opacity: 1; }
  50.01%, 100%  { opacity: 0.2; }
}

.composer-input {
  font-family: var(--font-body);
  font-size: 14px;
  border: none;
  padding: 10px 14px;
  resize: none;
  outline: none;
  background: transparent;
  color: var(--ink);
  caret-color: var(--phosphor);
  min-height: 48px;
}

.composer-send {
  border: none;
  border-left: 1px solid var(--line);
  background: transparent;
  color: var(--phosphor);
  font-family: var(--font-display);
  font-size: 22px;
  padding: 0 22px;
  cursor: pointer;
  letter-spacing: 0.1em;
}
.composer-send:hover:not(:disabled) {
  background: var(--bg-sunk);
  text-shadow: var(--glow-soft);
}
.composer-send:disabled {
  color: var(--ink-faint);
  cursor: not-allowed;
}
.composer-send::before { content: "▶ "; font-size: 16px; }

/* Errors */

.error-banner {
  background: #1a0808;
  color: var(--danger);
  padding: 6px 16px;
  font-family: var(--font-display);
  font-size: 16px;
  border-top: 1px solid #3a1a1a;
  letter-spacing: 0.1em;
}
.error-banner::before { content: "ERR │ "; color: var(--danger); opacity: 0.7; }
```

- [ ] **Step 2:** Commit

```bash
git add frontend/styles/terminal.css
git commit -m "feat(ui): add terminal-aesthetic stylesheet"
```

---

## Task 5: Point `index.html` at the new stylesheet

**File:** `frontend/index.html`

- [ ] **Step 1:** Change line 7 from:

```html
  <link rel="stylesheet" href="/styles/brutalist.css" />
```

to:

```html
  <link rel="stylesheet" href="/styles/terminal.css" />
```

- [ ] **Step 2:** Commit

```bash
git add frontend/index.html
git commit -m "feat(ui): switch stylesheet link to terminal.css"
```

---

## Task 6: Visual verification

Before deleting the old stylesheet, prove the new one works end-to-end against the live app.

- [ ] **Step 1:** Start the app

```powershell
.\start-boardroom.ps1
```

Open `http://127.0.0.1:8765/` in Chrome.

- [ ] **Step 2:** Checklist (compare against `docs/terminal-preview.html` for reference)

- Sidebar renders with `▶ AI BOARDROOM` in phosphor green, VT323 pixel font
- `├─` tree characters appear before each sidebar field label
- Room header shows `ROOM # main` with muted ROOM label and glowing `# main` title
- Participant strip on the right shows four outlined chips, each in its own color (amber User, green Codex, orange Claude, cyan Gemini)
- Existing messages render as flat dark cards with a 2px left-border stripe in the sender's color; sender names show as `[User]`, `[Codex]`, etc. in the sender color
- Composer at the bottom has a blinking `$` prompt on the left and a phosphor `▶ SEND` button on the right
- A subtle scanline overlay is visible across the whole viewport
- Layout is two-column — sidebar ~280px, main fills the rest. No empty dead zone on the right.

- [ ] **Step 3:** Post one test message via the composer

Type `@all terminal style check` and press Enter. Expected: message appears with sender User, amber stripe, in the list.

- [ ] **Step 4:** Run the existing Playwright DOM-contract tests to confirm nothing structural broke

```powershell
.\.venv\Scripts\Activate.ps1
pytest tests/test_dom_contract.py -v
```

Expected: all tests pass. These tests check `data-*` attributes, not visual styling, so a CSS swap should not affect them.

- [ ] **Step 5 (if any checklist item fails):** Fix only the affected selectors in `terminal.css`. Do not modify components or HTML. Commit fixes individually with descriptive messages.

---

## Task 7: Delete `brutalist.css`

Only after Task 4 passes cleanly.

- [ ] **Step 1:** Remove the old stylesheet

```bash
git rm frontend/styles/brutalist.css
```

- [ ] **Step 2:** Grep for any remaining references to confirm nothing else imports it

```powershell
Get-ChildItem -Recurse -File .\frontend, .\backend, .\tests, .\docs, .\*.md, .\*.ps1 |
    Select-String -Pattern "brutalist"
```

Expected: no matches in app code, docs, or root scripts.

- [ ] **Step 3:** Commit

```bash
git commit -m "chore(ui): remove unused brutalist.css"
```

---

## Task 8: Align plan and concept docs with reality

The plan files and concept doc already describe the terminal aesthetic, but the repo still links `frontend/styles/brutalist.css` in `frontend/index.html` today. Treat this task as both a doc reconciliation pass and a final code-vs-plan alignment check.

Verify they are still accurate:

- [ ] **Step 1:** Confirm `docs/AI_Boardroom_application-concept.md` §"Visual Design Direction" describes the terminal aesthetic (already done in an earlier edit; quick re-read).

- [ ] **Step 2:** Confirm `docs/superpowers/plans/2026-04-19-ai-boardroom-mvp/phase-6-app-assembly.md` Task 19 matches the CSS that actually shipped.

- [ ] **Step 3:** If discrepancies are found, edit the docs to match the shipped CSS exactly (the code is authoritative at this point, not the plan).

- [ ] **Step 4:** Commit any doc edits

```bash
git add docs/
git commit -m "docs: reconcile plan/concept with shipped terminal.css"
```

---

## Acceptance

This update is complete when:

- `frontend/styles/terminal.css` exists and is linked from `index.html`
- `frontend/styles/brutalist.css` no longer exists
- `frontend/vendor/fonts/` contains three committed woff2 files
- `.gitignore` allows `frontend/vendor/fonts/**` to be committed while still ignoring `frontend/vendor/vue.esm-browser.prod.js`
- `docs/terminal-preview.html` uses a neutral public-safe example path
- The live app at `http://127.0.0.1:8765/` renders the terminal aesthetic matching `docs/terminal-preview.html`
- `pytest tests/test_dom_contract.py` is green
- `git log` shows the expected commits for ignore-rule update, committed fonts, preview scrub, stylesheet creation, link swap, optional CSS fixes, brutalist removal, and any final doc reconciliation
- The `#app` / `.app-shell` grid bug found in the preview is fixed in the shipped CSS (`display: contents` on `#app`, grid on `.app-shell`)

---

## Rollback

If the terminal aesthetic causes problems in the wild, reverting is one `git revert` per commit — `brutalist.css` can be brought back from history and `index.html` pointed at it. The JSON session data and component DOM are unchanged, so no data migration is involved.
