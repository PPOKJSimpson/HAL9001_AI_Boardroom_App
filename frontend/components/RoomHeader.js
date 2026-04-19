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
