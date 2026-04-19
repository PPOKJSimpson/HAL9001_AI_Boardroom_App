function normalizeSenderType(sender) {
  return sender === "User" ? "human" : "agent";
}

export const Composer = {
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
        const senderType = normalizeSenderType(sender);

        await this.$emit("send", {
          sender,
          senderType,
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
