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
