# Phase 6 — App Assembly & Styling

**Prerequisites:** [Phase 5 — Frontend Components](phase-5-frontend-components.md) complete. All six component files must exist and export valid definitions. `setup.ps1` must have produced `frontend/vendor/vue.esm-browser.prod.js` — the app loads Vue from the vendored copy, not a CDN.

**Phase Goal:** Assemble the Vue application — wire session bootstrap, polling, and send handler in `app.js`; replace the placeholder `index.html` with the real document shell; and deliver the neo-brutalist stylesheet. At the end of this phase the app is visually complete and works end-to-end in Chrome.

**Completion Criteria:**
- Chrome loads `http://127.0.0.1:8765/` with no console errors
- Empty room renders with sidebar, room header, participant strip, and composer
- Typing `@all hi` in the composer and pressing Enter creates `msg-001` visible in the room
- Layout shows thick black borders, hard shadows on messages, and distinct participant chip colors
- `/api/messages` posted from another PowerShell window (see Phase 7) appears within ~1.5s without reload

**Next Phase:** [Phase 7 — Verification & CLI Prompts](phase-7-verification.md)

---

## Task 18: App Shell and Polling Loop

**Files:**
- Create: `frontend/app.js`
- Modify: `frontend/index.html`

- [ ] **Step 1: Implement app.js**

Create `frontend/app.js`:

```javascript
import { createApp } from "/vendor/vue.esm-browser.prod.js";
import { api } from "/api.js";
import { SessionSidebar } from "/components/SessionSidebar.js";
import { RoomHeader } from "/components/RoomHeader.js";
import { MessageList } from "/components/MessageList.js";
import { Composer } from "/components/Composer.js";

const POLL_INTERVAL_MS = 1500;

const App = {
  components: { SessionSidebar, RoomHeader, MessageList, Composer },
  data() {
    return {
      session: null,
      participants: [],
      messages: [],
      error: null,
      pollHandle: null,
    };
  },
  async mounted() {
    await this.bootstrap();
    this.startPolling();
    this.$nextTick(() => this.scrollToBottom());
  },
  beforeUnmount() {
    this.stopPolling();
  },
  methods: {
    async bootstrap() {
      try {
        const [session, participants, messages] = await Promise.all([
          api.getSession(),
          api.getParticipants(),
          api.getMessages(),
        ]);
        this.session = session;
        this.participants = participants;
        this.messages = messages;
      } catch (e) {
        this.error = e.message;
      }
    },
    startPolling() {
      this.pollHandle = setInterval(this.refreshMessages, POLL_INTERVAL_MS);
    },
    stopPolling() {
      if (this.pollHandle) clearInterval(this.pollHandle);
      this.pollHandle = null;
    },
    async refreshMessages() {
      try {
        const latest = await api.getMessages();
        const wasAtBottom = this.isScrolledToBottom();
        const hadNewMessage = latest.length > this.messages.length;
        this.messages = latest;
        if (wasAtBottom && hadNewMessage) {
          this.$nextTick(() => this.scrollToBottom());
        }
      } catch (e) {
        this.error = e.message;
      }
    },
    async handleSend({ sender, senderType, text, mentions }) {
      // sender/senderType come from Composer — defaults to User/human, but
      // honors the form's data-post-as attribute so browser-driven agents
      // can post under their own identity via the DOM write path.
      const stored = await api.postMessage({
        sender,
        senderType,
        text,
        mentions,
        replyTo: null,
      });
      this.messages.push(stored);
      this.$nextTick(() => this.scrollToBottom());
    },
    isScrolledToBottom() {
      const el = this.$refs.scroll;
      if (!el) return true;
      return el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    },
    scrollToBottom() {
      const el = this.$refs.scroll;
      if (el) el.scrollTop = el.scrollHeight;
    },
  },
  template: `
    <div class="app-shell">
      <SessionSidebar :session="session" />
      <main class="room-main">
        <RoomHeader
          :room-name="session?.roomName || 'main'"
          :participants="participants"
        />
        <div class="room-scroll" ref="scroll">
          <MessageList :messages="messages" />
        </div>
        <Composer @send="handleSend" />
        <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
      </main>
    </div>
  `,
};

createApp(App).mount("#app");
```

- [ ] **Step 2: Update index.html**

Replace the contents of `frontend/index.html` with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Boardroom</title>
  <link rel="stylesheet" href="/styles/brutalist.css" />
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Manual smoke check**

Start `./run.ps1`, open `http://127.0.0.1:8765/` in Chrome.

Expected:
- Page loads without console errors (styles missing is fine at this point)
- Empty room message visible
- Typing in the composer and pressing Enter adds a message
- Reloading the page preserves the message

- [ ] **Step 4: Commit**

```bash
git add frontend/app.js frontend/index.html
git commit -m "feat: Vue app shell with polling and message composer"
```

---

## Task 19: Neo-Brutalist Styling

**Files:**
- Create: `frontend/styles/brutalist.css`

- [ ] **Step 1: Write the stylesheet**

Create `frontend/styles/brutalist.css`:

```css
:root {
  --ink: #0a0a0a;
  --paper: #f2efe6;
  --panel: #ffffff;
  --border: 3px solid var(--ink);
  --border-thick: 4px solid var(--ink);
  --accent-user: #ffd400;
  --accent-codex: #00c2a8;
  --accent-claude: #d97a2d;
  --accent-gemini: #4a6ee0;
  --accent-system: #bbbbbb;
  --font-mono: "JetBrains Mono", "Cascadia Mono", Consolas, monospace;
  --font-display: "Space Grotesk", "Helvetica Neue", Arial, sans-serif;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  height: 100%;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--font-mono);
  font-size: 15px;
  line-height: 1.45;
}

#app, .app-shell {
  height: 100vh;
  display: grid;
  grid-template-columns: 280px 1fr;
}

.session-sidebar {
  background: var(--panel);
  border-right: var(--border-thick);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.sidebar-header {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.06em;
  border-bottom: var(--border);
  padding-bottom: 10px;
}

.session-facts { margin: 0; display: grid; gap: 6px; }
.session-facts dt {
  font-size: 11px;
  letter-spacing: 0.18em;
  opacity: 0.7;
}
.session-facts dd {
  margin: 0 0 10px 0;
  font-weight: 600;
  word-break: break-all;
}

.room-main {
  display: grid;
  grid-template-rows: auto 1fr auto;
  min-height: 0;
}

.room-header {
  border-bottom: var(--border-thick);
  padding: 16px 20px;
  background: var(--panel);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.room-label {
  font-size: 11px;
  letter-spacing: 0.22em;
  opacity: 0.7;
}

.room-title {
  font-family: var(--font-display);
  font-size: 34px;
  font-weight: 800;
  margin: 0;
  text-transform: lowercase;
}

.participant-strip {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.participant-chip {
  border: var(--border);
  padding: 6px 10px;
  background: var(--panel);
  display: inline-flex;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  font-weight: 700;
}

.participant-chip .participant-role {
  font-weight: 400;
  opacity: 0.65;
  font-size: 11px;
}

.participant-name-user    { background: var(--accent-user); }
.participant-name-codex   { background: var(--accent-codex); color: var(--paper); }
.participant-name-claude  { background: var(--accent-claude); color: var(--paper); }
.participant-name-gemini  { background: var(--accent-gemini); color: var(--paper); }

.room-scroll {
  overflow-y: auto;
  padding: 20px;
  background: var(--paper);
  min-height: 0;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message {
  border: var(--border);
  background: var(--panel);
  padding: 12px 14px;
  max-width: 760px;
  box-shadow: 6px 6px 0 0 var(--ink);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
  gap: 12px;
}

.sender {
  font-weight: 800;
  font-family: var(--font-display);
  font-size: 15px;
  letter-spacing: 0.02em;
}

.sender-user    { color: var(--ink); background: var(--accent-user); padding: 2px 6px; }
.sender-codex   { color: var(--paper); background: var(--accent-codex); padding: 2px 6px; }
.sender-claude  { color: var(--paper); background: var(--accent-claude); padding: 2px 6px; }
.sender-gemini  { color: var(--paper); background: var(--accent-gemini); padding: 2px 6px; }

time {
  font-size: 12px;
  opacity: 0.7;
}

.message-body {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.empty-room {
  text-align: center;
  padding: 40px;
  opacity: 0.6;
  font-size: 14px;
  letter-spacing: 0.08em;
}

.composer {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0;
  border-top: var(--border-thick);
  background: var(--panel);
}

.composer-input {
  font-family: var(--font-mono);
  font-size: 15px;
  border: none;
  padding: 14px 16px;
  resize: none;
  outline: none;
  background: var(--panel);
  color: var(--ink);
}

.composer-input:focus {
  background: #fff8d6;
}

.composer-send {
  border: none;
  border-left: var(--border-thick);
  background: var(--ink);
  color: var(--paper);
  font-family: var(--font-display);
  font-weight: 800;
  letter-spacing: 0.15em;
  padding: 0 28px;
  cursor: pointer;
  font-size: 14px;
}

.composer-send:disabled {
  background: #6a6a6a;
  cursor: not-allowed;
}

.error-banner {
  background: #b50000;
  color: var(--paper);
  padding: 8px 16px;
  font-weight: 700;
  border-top: var(--border-thick);
}
```

- [ ] **Step 2: Manual visual check**

Restart `./run.ps1`, reload Chrome.

Expected:
- Two-column layout with sidebar + main pane
- Thick black borders, hard shadows on messages
- Yellow/teal/orange/blue participant chips
- Composer at bottom with black SEND button

- [ ] **Step 3: Commit**

```bash
git add frontend/styles/brutalist.css
git commit -m "feat: neo-brutalist styling"
```
