export const ParticipantStrip = {
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
