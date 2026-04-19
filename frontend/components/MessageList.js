import { MessageItem } from "./MessageItem.js";

export const MessageList = {
  components: { MessageItem },
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
