<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  ApiError,
  coordinatorApi,
  type AssignmentDetail,
  type Proposal,
  type ShiftDetail,
} from '@/api'
import { formatDay, formatTimeRange, groupByDay } from '@/time'

const props = defineProps<{ clubId: string; token: string }>()
const clubId = computed(() => Number(props.clubId))

const shifts = ref<ShiftDetail[]>([])
const assignments = ref<AssignmentDetail[]>([])
const balances = ref(new Map<number, number>())
const proposal = ref<Proposal | null>(null)
const phase = ref<'loading' | 'error' | 'ready' | 'generating' | 'preview' | 'publishing'>(
  'loading',
)
const published = ref(false)
const loadError = ref('')
const actionError = ref('')

const errorText = (error: unknown) =>
  error instanceof ApiError ? error.message : 'Could not reach the server.'

async function load() {
  phase.value = 'loading'
  try {
    const [allShifts, allAssignments, ledger] = await Promise.all([
      coordinatorApi.shifts(clubId.value),
      coordinatorApi.assignments(clubId.value),
      coordinatorApi.ledger(clubId.value),
    ])
    shifts.value = allShifts
    assignments.value = allAssignments
    balances.value = new Map(ledger.balances.map((b) => [b.member_id, b.balance]))
    proposal.value = null
    phase.value = 'ready'
  } catch (error) {
    loadError.value = errorText(error)
    phase.value = 'error'
  }
}

async function generate() {
  phase.value = 'generating'
  actionError.value = ''
  published.value = false
  try {
    proposal.value = await coordinatorApi.generate(clubId.value, props.token)
    phase.value = 'preview'
  } catch (error) {
    actionError.value = errorText(error)
    phase.value = proposal.value ? 'preview' : 'ready'
  }
}

async function publish() {
  phase.value = 'publishing'
  actionError.value = ''
  try {
    await coordinatorApi.publish(clubId.value, props.token)
    await load()
    published.value = true
  } catch (error) {
    actionError.value = errorText(error)
    phase.value = 'preview'
  }
}

const busy = computed(() => phase.value === 'generating' || phase.value === 'publishing')
const withPoints = (memberId: number, name: string) =>
  `${name} (${balances.value.get(memberId) ?? 0} pts)`

/** Who already holds each shift, from earlier publishes. */
const holders = computed(() => {
  const map = new Map<number, string[]>()
  for (const a of assignments.value) {
    map.set(a.shift_id, [...(map.get(a.shift_id) ?? []), withPoints(a.member_id, a.member_name)])
  }
  return map
})

// Mirrors the backend rule: only shifts that haven't started yet can be scheduled.
const upcoming = computed(() => {
  const now = Date.now()
  return shifts.value.filter((s) => new Date(s.starts_at).getTime() > now)
})

const openShifts = computed(() =>
  upcoming.value
    .map((s) => {
      const held = holders.value.get(s.id) ?? []
      return { ...s, held, missing: s.slots - held.length }
    })
    .filter((s) => s.missing > 0),
)
const emptySlots = computed(() => openShifts.value.reduce((sum, s) => sum + s.missing, 0))
const fullyStaffed = computed(() => upcoming.value.length - openShifts.value.length)
const openDays = computed(() => groupByDay(openShifts.value))

const previewRows = computed(() => {
  if (!proposal.value) return []
  const added = new Map<number, string[]>()
  for (const a of proposal.value.assignments) {
    added.set(a.shift_id, [
      ...(added.get(a.shift_id) ?? []),
      withPoints(a.member_id, a.member_name),
    ])
  }
  const missing = new Map(proposal.value.unfilled.map((u) => [u.shift_id, u.missing]))
  return shifts.value
    .filter((s) => added.has(s.id) || missing.has(s.id))
    .map((s) => ({
      ...s,
      held: holders.value.get(s.id) ?? [],
      added: added.get(s.id) ?? [],
      missing: missing.get(s.id) ?? 0,
    }))
})

const gapRows = computed(() => previewRows.value.filter((row) => row.missing > 0))
const totalMissing = computed(() => gapRows.value.reduce((sum, row) => sum + row.missing, 0))
const previewDays = computed(() => groupByDay(previewRows.value))

onMounted(load)
</script>

<template>
  <main class="page-wide">
    <p v-if="phase === 'loading'" class="muted">Loading shifts…</p>

    <section v-else-if="phase === 'error'">
      <h1>Couldn't load the schedule</h1>
      <p class="muted">{{ loadError }}</p>
      <button type="button" @click="load">Try again</button>
    </section>

    <template v-else>
      <header class="intro">
        <h1>Schedule</h1>
        <p class="muted">
          {{ openShifts.length }} upcoming
          {{ openShifts.length === 1 ? 'shift needs' : 'shifts need' }} people ({{
            emptySlots
          }}
          empty {{ emptySlots === 1 ? 'slot' : 'slots' }}) · {{ fullyStaffed }} fully staffed
        </p>
      </header>

      <p v-if="published" class="ok" role="status">Published. Members can now see their shifts.</p>
      <p v-if="actionError" class="error" role="alert">{{ actionError }}</p>

      <!-- Before generating: what still needs people -->
      <template v-if="!proposal">
        <p v-if="upcoming.length === 0" class="muted">
          No upcoming shifts.
          <RouterLink :to="{ name: 'setup', params: { clubId, token } }"
            >Add some in Setup</RouterLink
          >.
        </p>
        <p v-else-if="openShifts.length === 0" class="muted">
          Every upcoming shift has enough people.
        </p>

        <template v-else>
          <div class="actions">
            <button type="button" :disabled="busy" @click="generate">
              {{ phase === 'generating' ? 'Generating…' : 'Generate a schedule' }}
            </button>
            <p class="muted">Nothing is saved until you publish.</p>
          </div>

          <section v-for="group in openDays" :key="group.day" class="day">
            <h2>{{ group.day }}</h2>
            <article v-for="shift in group.items" :key="shift.id" class="shift">
              <div class="shift-head">
                <span class="shift-name">{{ shift.shift_type }}</span>
                <span class="muted">{{ formatTimeRange(shift.starts_at, shift.ends_at) }}</span>
                <span class="muted">{{ shift.held.length }} of {{ shift.slots }} filled</span>
              </div>
              <p class="people">{{ shift.held.length ? shift.held.join(', ') : 'Nobody yet' }}</p>
            </article>
          </section>
        </template>
      </template>

      <!-- After generating: the proposal -->
      <template v-else>
        <section class="gaps" :class="{ 'gaps-none': totalMissing === 0 }" aria-live="polite">
          <h2 v-if="totalMissing === 0">Every slot can be filled</h2>
          <template v-else>
            <h2>
              {{ totalMissing }} {{ totalMissing === 1 ? 'slot still needs' : 'slots still need' }}
              a volunteer
            </h2>
            <ul>
              <li v-for="row in gapRows" :key="row.id">
                <strong>{{ row.shift_type }}</strong
                >, {{ formatDay(row.starts_at) }},
                {{ formatTimeRange(row.starts_at, row.ends_at) }}: {{ row.missing }} missing
              </li>
            </ul>
            <p>
              Ask around in the club chat. You can publish now and generate again later: open slots
              stay open until someone is available.
            </p>
          </template>
        </section>

        <section v-for="group in previewDays" :key="group.day" class="day">
          <h2>{{ group.day }}</h2>
          <article
            v-for="row in group.items"
            :key="row.id"
            class="shift"
            :class="{ 'has-gap': row.missing > 0 }"
          >
            <div class="shift-head">
              <span class="shift-name">{{ row.shift_type }}</span>
              <span class="muted">{{ formatTimeRange(row.starts_at, row.ends_at) }}</span>
              <span class="muted">
                {{ row.held.length + row.added.length }} of {{ row.slots }} filled
              </span>
            </div>
            <p v-if="row.held.length || row.added.length" class="people">
              <span v-for="name in row.held" :key="`held-${name}`" class="person">{{ name }}</span>
              <span v-for="name in row.added" :key="`new-${name}`" class="person">
                {{ name }} <span class="tag-new">new</span>
              </span>
            </p>
            <p v-if="row.missing > 0" class="gap-note">{{ row.missing }} missing</p>
          </article>
        </section>

        <div class="actions">
          <button type="button" class="button-secondary" :disabled="busy" @click="generate">
            Generate again
          </button>
          <button type="button" :disabled="busy" @click="publish">
            {{ phase === 'publishing' ? 'Publishing…' : 'Publish schedule' }}
          </button>
        </div>
      </template>
    </template>
  </main>
</template>

<style scoped>
.intro,
.day {
  margin-bottom: var(--space-6);
}
h2 {
  font-size: 1.125rem;
  margin: 0 0 var(--space-3);
}
.gaps {
  border: 2px solid var(--color-warning);
  background: var(--color-warning-surface);
  border-radius: var(--radius);
  padding: var(--space-4);
  margin-bottom: var(--space-6);
}
.gaps.gaps-none {
  border-color: var(--color-ok);
  background: transparent;
}
.gaps ul {
  margin: 0 0 var(--space-3);
  padding-left: var(--space-6);
}
.gaps p {
  margin: 0;
}
.shift {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-2);
}
.shift.has-gap {
  border-color: var(--color-warning);
  border-left-width: 4px;
}
.shift-head {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-4);
}
.shift-name {
  font-weight: 600;
}
.people {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1, 4px) var(--space-3);
  margin: var(--space-2) 0 0;
}
.tag-new {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-accent);
}
.gap-note {
  margin: var(--space-2) 0 0;
  color: var(--color-warning);
  font-weight: 600;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  margin: var(--space-4) 0;
}
.actions p {
  margin: 0;
}
.ok {
  color: var(--color-ok);
}
</style>
