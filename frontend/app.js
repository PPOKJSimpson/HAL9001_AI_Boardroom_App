import { createApp } from "/vendor/vue.esm-browser.prod.js";
import { api } from "/api.js";

const POLL_INTERVAL_MS = 1500;

function normalizeSenderType(sender) {
  return sender === "User" ? "human" : "agent";
}

async function loadModule(path) {
  try {
    return await import(path);
  } catch (error) {
    console.warn(`Failed to import ${path}; using fallback component.`, error);
    return null;
  }
}

const FallbackMessageItem = {
  props: {
    message: { type: Object, required: true },
  },
  computed: {
    mentionsAttr() {
      return (this.message.mentions || []).join(",");
    },
    shortTime() {
      const date = new Date(this.message.timestamp);
      if (Number.isNaN(date.getTime())) {
        return this.message.timestamp || "";
      }
      return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
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

const FallbackMessageList = {
  components: { MessageItem: FallbackMessageItem },
  props: {
    messages: { type: Array, required: true },
  },
  template: `
    <section class="message-list" aria-label="Conversation">
      <MessageItem
        v-for="message in messages"
        :key="message.id"
        :message="message"
      />
      <div v-if="messages.length === 0" class="empty-room">
        No messages yet. Post the first one below.
      </div>
    </section>
  `,
};

const FallbackComposer = {
  emits: ["send"],
  data() {
    return {
      text: "",
      sending: false,
    };
  },
  computed: {
    canSend() {
      return !this.sending && this.text.trim().length > 0;
    },
    parsedMentions() {
      const matches = this.text.match(/@([a-zA-Z0-9_-]+)/g) || [];
      return matches.map((match) => match.slice(1).toLowerCase());
    },
  },
  methods: {
    async submit() {
      if (!this.canSend) {
        return;
      }
      this.sending = true;
      try {
        const sender = this.$el.dataset.postAs || "User";
        await this.$emit("send", {
          sender,
          senderType: normalizeSenderType(sender),
          text: this.text.trim(),
          mentions: this.parsedMentions,
        });
        this.text = "";
        this.$el.dataset.postAs = "User";
      } finally {
        this.sending = false;
      }
    },
    onKeydown(event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
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

const FallbackParticipantStrip = {
  props: {
    participants: { type: Array, required: true },
  },
  template: `
    <ul class="participant-strip" aria-label="Participants">
      <li
        v-for="participant in participants"
        :key="participant.name"
        class="participant-chip"
        :class="'participant-' + participant.type + ' participant-name-' + participant.name.toLowerCase()"
        :data-participant-name="participant.name"
        :data-participant-type="participant.type"
      >
        <span class="participant-name">{{ participant.name }}</span>
        <span v-if="participant.role" class="participant-role">{{ participant.role }}</span>
      </li>
    </ul>
  `,
};

const FallbackRoomHeader = {
  components: { ParticipantStrip: FallbackParticipantStrip },
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

const FallbackSessionSidebar = {
  props: {
    session: { type: Object, default: null },
  },
  computed: {
    sessionId() {
      return this.session?.id || "—";
    },
    roomName() {
      return this.session?.roomName || "—";
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
        <dd>{{ sessionId }}</dd>
        <dt>ROOM</dt>
        <dd>{{ roomName }}</dd>
        <dt>PROJECT</dt>
        <dd class="session-path">{{ projectPath }}</dd>
      </dl>
    </aside>
  `,
};

const [
  messageListModule,
  composerModule,
  roomHeaderModule,
  sessionSidebarModule,
] = await Promise.all([
  loadModule("/components/MessageList.js"),
  loadModule("/components/Composer.js"),
  loadModule("/components/RoomHeader.js"),
  loadModule("/components/SessionSidebar.js"),
]);

const MessageList = messageListModule?.MessageList || FallbackMessageList;
const Composer = composerModule?.Composer || FallbackComposer;
const RoomHeader = roomHeaderModule?.RoomHeader || FallbackRoomHeader;
const SessionSidebar = sessionSidebarModule?.SessionSidebar || FallbackSessionSidebar;

const App = {
  components: { SessionSidebar, RoomHeader, MessageList, Composer },
  data() {
    return {
      session: null,
      participants: [],
      messages: [],
      error: null,
      pollHandle: null,
      refreshInFlight: false,
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
        this.error = null;
      } catch (error) {
        this.error = error.message;
      }
    },
    startPolling() {
      if (this.pollHandle) {
        return;
      }
      this.pollHandle = window.setInterval(() => {
        this.refreshMessages();
      }, POLL_INTERVAL_MS);
    },
    stopPolling() {
      if (this.pollHandle) {
        window.clearInterval(this.pollHandle);
      }
      this.pollHandle = null;
    },
    async refreshMessages() {
      if (this.refreshInFlight) {
        return;
      }
      this.refreshInFlight = true;
      try {
        const latest = await api.getMessages();
        const wasAtBottom = this.isScrolledToBottom();
        const hadNewMessage = latest.length > this.messages.length;
        this.messages = latest;
        this.error = null;
        if (wasAtBottom && hadNewMessage) {
          this.$nextTick(() => this.scrollToBottom());
        }
      } catch (error) {
        this.error = error.message;
      } finally {
        this.refreshInFlight = false;
      }
    },
    async handleSend({ sender, senderType, text, mentions }) {
      const stored = await api.postMessage({
        sender,
        senderType,
        text,
        mentions,
        replyTo: null,
      });
      this.messages.push(stored);
      this.error = null;
      this.$nextTick(() => this.scrollToBottom());
    },
    isScrolledToBottom() {
      const element = this.$refs.scroll;
      if (!element) {
        return true;
      }
      return element.scrollHeight - element.scrollTop - element.clientHeight < 40;
    },
    scrollToBottom() {
      const element = this.$refs.scroll;
      if (element) {
        element.scrollTop = element.scrollHeight;
      }
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
