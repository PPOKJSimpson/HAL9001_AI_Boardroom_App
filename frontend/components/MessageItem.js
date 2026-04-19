export const MessageItem = {
  props: {
    message: { type: Object, required: true },
  },
  computed: {
    mentionsAttr() {
      return (this.message.mentions || []).join(",");
    },
    shortTime() {
      const date = new Date(this.message.timestamp);
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
