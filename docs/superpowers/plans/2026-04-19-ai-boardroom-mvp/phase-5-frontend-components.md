# Phase 5 — Frontend Components

**Prerequisites:** [Phase 4 — Frontend Delivery & API Client](phase-4-frontend-delivery.md) complete. `/api.js` must be importable from the browser and resolve API calls.

**Phase Goal:** Author every Vue 3 component the app needs. Each component file exports a single component definition object using in-browser template strings (no build step). The `MessageItem` component carries the full DOM contract attributes (`data-message-id`, `data-sender`, `data-sender-type`, `data-mentions`, `data-reply-to`, `data-timestamp`) that CLI participants will parse.

Components are authored in isolation here; wiring them together is Phase 6.

**Completion Criteria:**
- All six component files exist under `frontend/components/`
- Each file is a valid ES module with a named export matching its component name
- No behavioral test run at this phase — validation happens in Phase 6 (visual) and Phase 7 (Playwright)

**Next Phase:** [Phase 6 — App Assembly & Styling](phase-6-app-assembly.md)

---

## Task 13: MessageItem Component

**Files:**
- Create: `frontend/components/MessageItem.js`

- [ ] **Step 1: Implement MessageItem**

Create `frontend/components/MessageItem.js`:

```javascript
export const MessageItem = {
  props: {
    message: { type: Object, required: true },
  },
  computed: {
    mentionsAttr() {
      return (this.message.mentions || []).join(",");
    },
    shortTime() {
      const d = new Date(this.message.timestamp);
      return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    },
    senderClass() {
      return `sender sender-${(this.message.sender || "").toLowerCase()}`;
    },
  },
  template: `
    <article
      class="message"
      :class="'message-' + message.senderType"
      :data-message-id="message.id"
      :data-sender="message.sender"
      :data-sender-type="message.senderType"
      :data-mentions="mentionsAttr"
      :data-reply-to="message.replyTo || ''"
      :data-timestamp="message.timestamp"
    >
      <header class="message-header">
        <span :class="senderClass">{{ message.sender }}</span>
        <time :datetime="message.timestamp">{{ shortTime }}</time>
      </header>
      <div class="message-body">{{ message.text }}</div>
    </article>
  `,
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/MessageItem.js
git commit -m "feat: MessageItem component with DOM contract attributes"
```

---

## Task 14: MessageList Component

**Files:**
- Create: `frontend/components/MessageList.js`

- [ ] **Step 1: Implement MessageList**

Create `frontend/components/MessageList.js`:

```javascript
import { MessageItem } from "./MessageItem.js";

export const MessageList = {
  components: { MessageItem },
  props: {
    messages: { type: Array, required: true },
  },
  template: `
    <section class="message-list" aria-label="Conversation">
      <MessageItem
        v-for="m in messages"
        :key="m.id"
        :message="m"
      />
      <div v-if="messages.length === 0" class="empty-room">
        No messages yet. Post the first one below.
      </div>
    </section>
  `,
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/MessageList.js
git commit -m "feat: MessageList component"
```

---

## Task 15: Composer Component

**Composer contract (also used by CLI browser-automation):**

- Root element: `<form class="composer" data-post-as="User">`
- Input: `<textarea class="composer-input">` (bound with Vue `v-model` — a
  browser tool that sets `.value` programmatically must also dispatch an
  `input` event for Vue to capture the change)
- Submit button: `<button class="composer-send" type="submit">`
- The form's `data-post-as` attribute controls who the outgoing message is
  attributed to. Default is `"User"`. An agent's browser-automation flow
  may set it to `"Codex"`, `"Claude"`, or `"Gemini"` before submitting.
- After every successful submit, the composer resets `data-post-as` back to
  `"User"` so an agent's identity cannot leak into the next human post.

**Files:**
- Create: `frontend/components/Composer.js`

- [ ] **Step 1: Implement Composer**

Create `frontend/components/Composer.js`:

```javascript
function normalizeSenderType(sender) {
  // Map the limited participant set to sender types. User -> human,
  // everything else (Codex, Claude, Gemini, or any future named agent) -> agent.
  return sender === "User" ? "human" : "agent";
}

export const Composer = {
  emits: ["send"],
  data() {
    return { text: "", sending: false };
  },
  computed: {
    canSend() {
      return !this.sending && this.text.trim().length > 0;
    },
    parsedMentions() {
      const matches = this.text.match(/@([a-zA-Z0-9_-]+)/g) || [];
      return matches.map((m) => m.slice(1).toLowerCase());
    },
  },
  methods: {
    async submit() {
      if (!this.canSend) return;
      this.sending = true;
      try {
        const sender = this.$el.dataset.postAs || "User";
        const senderType = normalizeSenderType(sender);
        await this.$emit("send", {
          sender,
          senderType,
          text: this.text.trim(),
          mentions: this.parsedMentions,
        });
        this.text = "";
        // Reset identity so an agent's data-post-as does not leak into
        // later human posts. Agents must set data-post-as for each post.
        this.$el.dataset.postAs = "User";
      } finally {
        this.sending = false;
      }
    },
    onKeydown(evt) {
      if (evt.key === "Enter" && !evt.shiftKey) {
        evt.preventDefault();
        this.submit();
      }
    },
  },
  template: `
    <form class="composer" data-post-as="User" @submit.prevent="submit">
      <textarea
        class="composer-input"
        v-model="text"
        @keydown="onKeydown"
        placeholder="Type a message. Use @codex @claude @gemini @all to direct it."
        rows="2"
        aria-label="Message input"
      ></textarea>
      <button
        type="submit"
        class="composer-send"
        :disabled="!canSend"
        aria-label="Send message"
      >SEND</button>
    </form>
  `,
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/Composer.js
git commit -m "feat: Composer supports data-post-as for agent-identity posts"
```

---

## Task 16: ParticipantStrip Component

**Files:**
- Create: `frontend/components/ParticipantStrip.js`

- [ ] **Step 1: Implement ParticipantStrip**

Create `frontend/components/ParticipantStrip.js`:

```javascript
export const ParticipantStrip = {
  props: {
    participants: { type: Array, required: true },
  },
  template: `
    <ul class="participant-strip" aria-label="Participants">
      <li
        v-for="p in participants"
        :key="p.name"
        class="participant-chip"
        :class="'participant-' + p.type + ' participant-name-' + p.name.toLowerCase()"
        :data-participant-name="p.name"
        :data-participant-type="p.type"
      >
        <span class="participant-name">{{ p.name }}</span>
        <span v-if="p.role" class="participant-role">{{ p.role }}</span>
      </li>
    </ul>
  `,
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/ParticipantStrip.js
git commit -m "feat: ParticipantStrip component"
```

---

## Task 17: RoomHeader and SessionSidebar Components

**Files:**
- Create: `frontend/components/RoomHeader.js`
- Create: `frontend/components/SessionSidebar.js`

- [ ] **Step 1: Implement RoomHeader**

Create `frontend/components/RoomHeader.js`:

```javascript
import { ParticipantStrip } from "./ParticipantStrip.js";

export const RoomHeader = {
  components: { ParticipantStrip },
  props: {
    roomName: { type: String, required: true },
    participants: { type: Array, required: true },
  },
  template: `
    <header class="room-header" :data-room-name="roomName">
      <div class="room-title-block">
        <span class="room-label">ROOM</span>
        <h1 class="room-title">{{ roomName }}</h1>
      </div>
      <ParticipantStrip :participants="participants" />
    </header>
  `,
};
```

- [ ] **Step 2: Implement SessionSidebar**

Create `frontend/components/SessionSidebar.js`:

```javascript
export const SessionSidebar = {
  props: {
    session: { type: Object, default: null },
  },
  computed: {
    shortId() {
      return this.session?.id || "—";
    },
    projectPath() {
      return this.session?.projectPath || "—";
    },
  },
  template: `
    <aside class="session-sidebar" aria-label="Session info">
      <div class="sidebar-header">AI BOARDROOM</div>
      <dl class="session-facts">
        <dt>SESSION</dt>
        <dd>{{ shortId }}</dd>
        <dt>ROOM</dt>
        <dd>{{ session?.roomName || '—' }}</dd>
        <dt>PROJECT</dt>
        <dd class="session-path">{{ projectPath }}</dd>
      </dl>
    </aside>
  `,
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/RoomHeader.js frontend/components/SessionSidebar.js
git commit -m "feat: RoomHeader and SessionSidebar components"
```
