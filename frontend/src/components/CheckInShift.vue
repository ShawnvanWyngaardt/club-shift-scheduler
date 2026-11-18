<script setup lang="ts">
import { computed } from 'vue'
import type { AssignmentDetail } from '@/api'
import type { CheckInGroup, Mark } from '@/checkin'
import { points } from '@/format'
import { formatDay, formatTimeRange } from '@/time'

/*
 * One shift on the Check-in page: a small card per person with a tick and a cross,
 * and Save for the whole shift. The marks live in the page, so they survive this
 * card re-rendering; this component only shows them and reports clicks.
 */
const props = defineProps<{
  group: CheckInGroup
  marks: ReadonlyMap<number, Mark>
  saving: boolean
  error: string
}>()
const emit = defineEmits<{ mark: [person: AssignmentDetail, outcome: Mark]; save: [] }>()

const OUTCOMES = [
  {
    value: 'done',
    cls: 'tick',
    label: 'did the shift',
    title: 'Did the shift',
    path: 'M3.5 8.5l3 3 6-7',
  },
  {
    value: 'no_show',
    cls: 'cross',
    label: 'missed the shift',
    title: 'Missed it',
    path: 'M4.5 4.5l7 7M11.5 4.5l-7 7',
  },
] as const

const ready = computed(() =>
  props.group.people.filter((p) => p.status === 'assigned' && props.marks.has(p.id)),
)
const checked = computed(() => props.group.people.filter((p) => p.status !== 'assigned').length)
const allSaved = computed(() => checked.value === props.group.people.length)

/** The outcome shown on a card: saved, or marked and not saved yet. */
const shown = (p: AssignmentDetail) =>
  p.status === 'assigned' ? props.marks.get(p.id) : p.status
</script>

<template>
  <section class="shift-group">
    <div class="shift-group-head">
      <div>
        <h2>{{ group.shiftType }}</h2>
        <span class="sg-when">
          {{ formatDay(group.startsAt) }},
          <span class="t">{{ formatTimeRange(group.startsAt, group.endsAt) }}</span>
          | {{ points(group.weight, { short: true }) }}
        </span>
      </div>
      <span class="sg-count">{{ checked }} of {{ group.people.length }} checked</span>
    </div>

    <div class="sg-body">
      <div class="people-grid">
        <div
          v-for="p in group.people"
          :key="p.id"
          class="person"
          :class="[shown(p), { saved: p.status !== 'assigned' }]"
        >
          <span class="person-name">{{ p.member_name }}</span>
          <span class="person-actions" role="group" :aria-label="`Check in ${p.member_name}`">
            <!-- Once saved, only the result stays, so it moves to the right edge -->
            <template v-for="o in OUTCOMES" :key="o.value">
              <button
                v-if="p.status === 'assigned' || p.status === o.value"
                type="button"
                class="mini-btn"
                :class="o.cls"
                :aria-pressed="shown(p) === o.value"
                :disabled="p.status !== 'assigned' || saving"
                :aria-label="`${p.member_name} ${o.label}`"
                :title="o.title"
                @click="emit('mark', p, o.value)"
              >
                <span class="mini" :class="o.cls">
                  <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
                    <path :d="o.path" />
                  </svg>
                </span>
              </button>
            </template>
          </span>
        </div>
      </div>

      <span v-if="allSaved" class="sg-saved">Saved</span>
      <button
        v-else
        type="button"
        class="btn btn-small btn-go sg-save-btn"
        :disabled="ready.length === 0 || saving"
        @click="emit('save')"
      >
        <template v-if="saving">Saving…</template>
        <template v-else>Save{{ ready.length ? ` (${ready.length})` : '' }}</template>
      </button>
    </div>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </section>
</template>

<style scoped>
.shift-group {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--line);
}
.shift-group-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px 16px;
  margin-bottom: 12px;
}
.shift-group-head h2 {
  margin: 0;
  font-size: 16px;
}
.sg-when,
.sg-count {
  font-size: 13px;
  color: var(--muted);
}
.sg-when .t {
  font-family: var(--font-time);
}
.sg-count {
  font-variant-numeric: tabular-nums;
}

/* Cards on the left, Save in its own column on the right: more cards wrap, the button stays put */
.sg-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 112px;
  align-items: start;
  gap: 16px;
}
.sg-save-btn {
  width: 112px;
  margin-top: 8px; /* centred on the first row of 48px cards */
}
.sg-saved {
  display: grid;
  place-items: center;
  height: 48px;
  font-size: 13px;
  font-weight: 600;
  color: var(--green-ink);
}

.people-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}
.person {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 8px 8px 14px;
  background: var(--surface);
  border-radius: var(--r);
  box-shadow: var(--shadow);
}
.person-name {
  font-size: 14px;
  font-weight: 600;
}
/* Marked, not saved yet: dashed. Saved: solid green for done; missed stays grey. */
.person.done:not(.saved) {
  outline: 2px dashed var(--green);
  outline-offset: -2px;
}
.person.no_show:not(.saved) {
  outline: 2px dashed var(--muted);
  outline-offset: -2px;
}
.person.done.saved {
  box-shadow:
    inset 0 0 0 2px var(--green),
    var(--shadow);
}
.person.no_show .person-name {
  color: var(--muted);
}
.person-actions {
  display: inline-flex;
  gap: 4px;
}
/* 32px to click, the tinted square inside stays small. Pressed fills it solid. */
.mini-btn {
  display: grid;
  place-items: center;
  width: 32px;
  min-height: 32px;
  height: 32px;
  padding: 0;
  border: 0;
  background: transparent;
}
.mini-btn:disabled {
  cursor: default;
}
.mini-btn.tick:not(:disabled):hover .mini,
.mini-btn.tick[aria-pressed='true'] .mini {
  background: var(--green);
  color: #fff;
}
.mini-btn.cross:not(:disabled):hover .mini,
.mini-btn.cross[aria-pressed='true'] .mini {
  background: #c62828;
  color: #fff;
}

.error {
  margin: 8px 0 0;
  font-size: 13px;
}

@media (max-width: 600px) {
  .sg-body {
    grid-template-columns: 1fr;
  }
  .sg-save-btn,
  .sg-saved {
    width: 100%;
  }
}
</style>
