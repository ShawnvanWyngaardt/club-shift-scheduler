<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ApiError, coordinatorApi, type AssignmentDetail } from '@/api'
import { checkInGroups, savedNotice, type CheckInGroup, type Mark } from '@/checkin'
import CheckInShift from '@/components/CheckInShift.vue'
import { useNotice } from '@/composables/useNotice'
import { useWaitingCount } from '@/composables/useWaitingCount'

const props = defineProps<{ clubId: string; token: string }>()
const clubId = computed(() => Number(props.clubId))
const { showNotice } = useNotice()
const { updateWaiting } = useWaitingCount()

const assignments = ref<AssignmentDetail[]>([])
const state = ref<'loading' | 'ready' | 'error'>('loading')
const loadError = ref('')

/*
 * Marks are kept here until Save, so they can still change. Saving sends a whole
 * shift at once to the batch endpoint: all saved, or none if one fails.
 */
const marks = reactive(new Map<number, Mark>())
const saving = ref<number | null>(null) // the shift being saved
const groupError = ref<{ shiftId: number; text: string } | null>(null)

// Groups stay on screen after saving, showing "Saved", until the page is opened again.
const groups = ref<{ started: CheckInGroup[]; upcoming: CheckInGroup[] }>({
  started: [],
  upcoming: [],
})

async function load() {
  state.value = 'loading'
  try {
    assignments.value = await coordinatorApi.assignments(clubId.value, props.token)
    groups.value = checkInGroups(assignments.value)
    marks.clear()
    updateWaiting(assignments.value)
    state.value = 'ready'
  } catch (error) {
    loadError.value = error instanceof ApiError ? error.message : 'Could not reach the server.'
    state.value = 'error'
  }
}

function mark(person: AssignmentDetail, outcome: Mark) {
  if (person.status !== 'assigned') return
  // Pressing the same button again clears the mark.
  if (marks.get(person.id) === outcome) marks.delete(person.id)
  else marks.set(person.id, outcome)
}

async function save(group: CheckInGroup) {
  const people = group.people.filter((p) => p.status === 'assigned' && marks.has(p.id))
  if (people.length === 0) return
  const outcomes = people.map((p) => ({ assignment_id: p.id, status: marks.get(p.id)! }))
  saving.value = group.shiftId
  groupError.value = null
  try {
    await coordinatorApi.recordOutcomes(clubId.value, outcomes, props.token)
    for (const p of people) {
      p.status = marks.get(p.id)!
      marks.delete(p.id)
    }
    updateWaiting(assignments.value)
    const notice = savedNotice(
      group.shiftType,
      outcomes.map((o) => o.status),
    )
    showNotice(notice.title, notice.detail)
  } catch (error) {
    const text = error instanceof ApiError ? error.message : 'Could not reach the server.'
    if (error instanceof ApiError && error.status === 409) {
      await load() // someone already checked one of them in: show what is saved now
    }
    groupError.value = { shiftId: group.shiftId, text: `Nothing was saved. ${text}` }
  } finally {
    saving.value = null
  }
}

onMounted(load)
</script>

<template>
  <main class="wrap">
    <p v-if="state === 'loading'" class="muted">Loading check-ins…</p>

    <section v-else-if="state === 'error'">
      <h1>Couldn't load check-ins</h1>
      <p class="muted">{{ loadError }}</p>
      <button type="button" class="btn btn-primary" @click="load">Try again</button>
    </section>

    <template v-else>
      <div class="page-head">
        <h1>Who did their shift?</h1>
      </div>

      <div class="checkin-legend">
        <p class="legend-final">
          Mark each person, then press Save for that shift. You can change your marks
          until you save; after that they're final, so check people in after the shift has
          happened.
        </p>
        <p>
          <span class="mini tick" aria-hidden="true">
            <svg viewBox="0 0 16 16" width="16" height="16">
              <path d="M3.5 8.5l3 3 6-7" />
            </svg>
          </span>
          <span>
            <b>Did the shift.</b> The shift's points are added to their balance, so they
            move further back in line for the next shifts. They see it as Done on their My
            shifts page.
          </span>
        </p>
        <p>
          <span class="mini cross" aria-hidden="true">
            <svg viewBox="0 0 16 16" width="16" height="16">
              <path d="M4.5 4.5l7 7M11.5 4.5l-7 7" />
            </svg>
          </span>
          <span>
            <b>Missed it.</b> The shift's points come off their balance, which moves them
            up in line. They see it as Missed on their My shifts page.
          </span>
        </p>
      </div>

      <p v-if="groups.started.length === 0" class="all-clear">
        Nobody is waiting to be checked in.
      </p>

      <CheckInShift
        v-for="group in groups.started"
        :key="group.shiftId"
        :group="group"
        :marks="marks"
        :saving="saving === group.shiftId"
        :error="groupError?.shiftId === group.shiftId ? groupError.text : ''"
        @mark="mark"
        @save="save(group)"
      />

      <details v-if="groups.upcoming.length" class="upcoming">
        <summary>Upcoming shifts ({{ groups.upcoming.length }})</summary>
        <p class="note">
          These haven't happened yet. Checking in early is allowed, so you can try the
          page out, but a check-in is final.
        </p>
        <CheckInShift
          v-for="group in groups.upcoming"
          :key="group.shiftId"
          :group="group"
          :marks="marks"
          :saving="saving === group.shiftId"
          :error="groupError?.shiftId === group.shiftId ? groupError.text : ''"
          @mark="mark"
          @save="save(group)"
        />
      </details>
    </template>
  </main>
</template>

<style scoped>
.page-head h1 {
  margin-bottom: 0;
}

.checkin-legend {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 28px;
  font-size: 12px;
  color: var(--muted);
}
.checkin-legend p {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
}
.checkin-legend p > span:last-child {
  flex: 1;
  min-width: 0;
}
.checkin-legend b {
  font-weight: 600;
  color: var(--ink);
}
/* The instruction first, a size up from the legend under it */
.checkin-legend .legend-final {
  margin-bottom: 4px;
  font-size: 13px;
}

.all-clear {
  padding: 16px;
  border-radius: var(--r);
  border: 1.5px dashed color-mix(in srgb, var(--green) 55%, transparent);
  background: color-mix(in srgb, var(--mint-surface) 60%, var(--surface));
}

.upcoming {
  margin: 8px 0 24px;
}
.upcoming summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--navy);
}
.note {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--muted);
}
</style>
