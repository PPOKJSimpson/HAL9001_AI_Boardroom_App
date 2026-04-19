function formatRelativeTimestamp(timestamp) {
  if (!timestamp) return "unknown";

  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export const SessionSidebar = {
  props: {
    session: { type: Object, default: null },
    sessions: { type: Array, default: () => [] },
  },
  emits: ["switch-session", "new-session", "rename-session"],
  data() {
    return {
      titleDraft: "",
      lastCommittedTitle: "",
    };
  },
  computed: {
    shortId() {
      return this.session?.id || "—";
    },
    projectPath() {
      return this.session?.projectPath || "—";
    },
    roomName() {
      return this.session?.roomName || "—";
    },
    inviteUrl() {
      const origin = globalThis.location?.origin || "http://127.0.0.1:8765";
      return `${origin}/`;
    },
    inviteInstruction() {
      return "Room: " + this.inviteUrl + " — check the DOM or GET /api/messages";
    },
    pastSessions() {
      const currentId = this.session?.id;
      return (this.sessions || []).filter((item) => item?.id && item.id !== currentId);
    },
  },
  watch: {
    session: {
      immediate: true,
      handler(nextSession) {
        const nextTitle = nextSession?.title || "";
        this.titleDraft = nextTitle;
        this.lastCommittedTitle = nextTitle;
      },
    },
  },
  methods: {
    emitRenameIfChanged() {
      if (!this.session?.id) return;

      const nextTitle = this.titleDraft.trim();
      const previousTitle = (this.lastCommittedTitle || "").trim();
      if (nextTitle === previousTitle) return;

      this.lastCommittedTitle = nextTitle;
      this.$emit("rename-session", {
        id: this.session.id,
        title: nextTitle,
      });
    },
    onTitleKeydown(event) {
      if (event.key !== "Enter") return;
      event.preventDefault();
      event.target.blur();
    },
    sessionDisplayTitle(item) {
      return item?.title?.trim() || item?.id || "—";
    },
    sessionTimestamp(item) {
      return formatRelativeTimestamp(item?.updatedAt || item?.createdAt);
    },
    sessionMessageCount(item) {
      const count = Number(item?.messageCount || 0);
      return Number.isFinite(count) ? count : 0;
    },
    switchSession(sessionId) {
      if (!sessionId || sessionId === this.session?.id) return;
      this.$emit("switch-session", sessionId);
    },
  },
  template: `
    <aside class="session-sidebar" aria-label="Session info">
      <div class="sidebar-header">AI BOARDROOM</div>

      <section class="session-current">
        <div class="session-current-label">CURRENT SESSION</div>
        <input
          class="session-title-input"
          type="text"
          v-model="titleDraft"
          placeholder="Untitled session"
          aria-label="Session title"
          @blur="emitRenameIfChanged"
          @keydown="onTitleKeydown"
        />

        <dl class="session-facts">
          <dt>SESSION</dt>
          <dd>{{ shortId }}</dd>
          <dt>ROOM</dt>
          <dd>{{ roomName }}</dd>
          <dt>PROJECT</dt>
          <dd class="session-path">{{ projectPath }}</dd>
        </dl>

        <button
          type="button"
          class="session-new-btn"
          @click="$emit('new-session')"
        >NEW SESSION</button>
      </section>

      <section v-if="pastSessions.length" class="session-history">
        <div class="session-section-label">PAST SESSIONS</div>
        <ul class="past-sessions" aria-label="Past sessions">
          <li v-for="item in pastSessions" :key="item.id">
            <button
              type="button"
              class="past-session-row"
              :class="{ current: item.id === session?.id }"
              :disabled="item.id === session?.id"
              @click="switchSession(item.id)"
            >
              <span class="past-session-main">{{ sessionDisplayTitle(item) }}</span>
              <span class="past-session-meta">{{ sessionTimestamp(item) }}</span>
              <span class="past-session-count">({{ sessionMessageCount(item) }} msgs)</span>
            </button>
          </li>
        </ul>
      </section>

      <section class="session-invite">
        <div class="session-section-label">INVITE</div>
        <pre class="invite-snippet"><code>{{ inviteInstruction }}</code></pre>
      </section>
    </aside>
  `,
};
