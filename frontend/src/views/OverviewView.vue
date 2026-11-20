<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  ApiError,
  coordinatorApi,
  type AssignmentDetail,
  type AvailabilityPair,
  type Ledger,
  type ShiftDetail,
} from '@/api'
import { waitingForCheckIn } from '@/checkin'
import { points } from '@/format'
import {
  firstInLine,
  needsYou,
  summariseWeeks,
  weekStatus,
  type Need,
  type WeekSummary,
} from '@/overview'
import { formatDay, weeksFrom } from '@/time'

const props = defineProps<{ clubId: string; token: string }>()
const params = computed(() => ({ clubId: props.clubId, token: props.token }))
const shiftsLink = computed(() => ({
  name: 'members',
  params: params.value,
  query: { section: 'shifts' },
}))

const shifts = ref<ShiftDetail[]>([])
const assignments = ref<AssignmentDetail[]>([])
const balances = ref<Ledger['balances']>([])
const pairs = ref<AvailabilityPair[]>([])
const state = ref<'loading' | 'ready' | 'error'>('loading')
const loadError = ref('')

async function load() {
  state.value = 'loading'
  try {
    const id = Number(props.clubId)
    const shown = weeksFrom(new Date().toISOString(), 4)
    const range = { from: shown[0]!.start, to: shown[shown.length - 1]!.end }
    const [allShifts, allAssignments, ledger, available] = await Promise.all([
      coordinatorApi.shifts(id),
      coordinatorApi.assignments(id, props.token),
      coordinatorApi.ledger(id, props.token),
      coordinatorApi.availability(id, props.token, range),
    ])
    shifts.value = allShifts
    assignments.value = allAssignments
    balances.value = ledger.balances
    pairs.value = available
    state.value = 'ready'
  } catch (error) {
    loadError.value = error instanceof ApiError ? error.message : 'Could not reach the server.'
    state.value = 'error'
  }
}

const weeks = computed(() =>
  summariseWeeks(
    weeksFrom(new Date().toISOString(), 4),
    shifts.value,
    assignments.value,
    pairs.value,
  ),
)
const needs = computed(() => needsYou(weeks.value, assignments.value))
const waiting = computed(() => waitingForCheckIn(assignments.value))
const lowest = computed(() => firstInLine(balances.value))

const totals = computed(() => ({
  slots: weeks.value.reduce((sum, w) => sum + w.slots, 0),
  filled: weeks.value.reduce((sum, w) => sum + w.filled, 0),
  published: weeks.value.filter((w) => w.published).length,
}))

/** The last planned shift, for the "add the next weeks" nudge. */
const lastShift = computed(() => shifts.value.at(-1)?.starts_at)

function needLink(need: Need) {
  return need.to.name === 'week'
    ? { name: 'week', params: { ...params.value, week: need.to.week } }
    : { name: need.to.name, params: params.value }
}

function pill(w: WeekSummary) {
  const status = weekStatus(w)
  if (status === 'full') return { cls: 'published', text: 'Published | full' }
  if (status === 'gaps') return { cls: 'empty', text: `Published | ${w.empty} empty` }
  return { cls: 'unpublished', text: status === 'unpublished' ? 'Not published' : 'No shifts' }
}

const percentFilled = (w: WeekSummary) => (w.slots ? Math.round((w.filled / w.slots) * 100) : 0)

onMounted(load)
</script>

<template>
  <main class="wrap">
    <p v-if="state === 'loading'" class="muted">Loading the next four weeks…</p>

    <section v-else-if="state === 'error'">
      <h1>Couldn't load the overview</h1>
      <p class="muted">{{ loadError }}</p>
      <button type="button" class="btn btn-primary" @click="load">Try again</button>
    </section>

    <template v-else>
      <div class="page-head">
        <div>
          <h1>Overview</h1>
          <p>
            The next four weeks, and what needs you first. Members see their shifts once
            you publish.
          </p>
        </div>
        <RouterLink class="btn btn-ghost" :to="shiftsLink">Add shifts</RouterLink>
      </div>

      <div class="overview">
        <div>
          <h2 class="section-title">Needs you</h2>
          <div class="needs">
            <div v-for="need in needs" :key="need.title" class="need" :class="need.kind">
              <div class="need-text">
                <strong>{{ need.title }}</strong>
                <span>{{ need.text }}</span>
              </div>
              <RouterLink
                class="btn btn-small"
                :class="need.kind === 'go' ? 'btn-go' : 'btn-primary'"
                :to="needLink(need)"
              >
                {{ need.action }}
              </RouterLink>
            </div>

            <div v-if="needs.length === 0" class="all-clear">
              <span class="all-clear-icon" aria-hidden="true">✓</span>
              <div>
                <strong>You're all caught up</strong>
                <span v-if="lastShift">
                  Every slot in the next four weeks has someone and everyone is checked
                  in. Shifts are planned until {{ formatDay(lastShift) }}, so
                  <RouterLink class="text-link" :to="shiftsLink"
                    >add the next weeks</RouterLink
                  >
                  before then.
                </span>
                <span v-else>
                  No shifts are planned yet.
                  <RouterLink class="text-link" :to="shiftsLink"
                    >Add your first shifts</RouterLink
                  >
                  to get started.
                </span>
              </div>
            </div>
          </div>

          <h2 class="section-title">Weeks</h2>
          <div class="weeks">
            <RouterLink
              v-for="w in weeks"
              :key="w.week.key"
              class="week"
              :class="weekStatus(w)"
              :to="{ name: 'week', params: { ...params, week: w.week.key } }"
            >
              <span>
                <span class="week-name">Week {{ w.week.number }}</span>
                <span class="week-dates">{{ w.week.dates }}</span>
              </span>
              <span class="week-mid">
                <span
                  class="meter"
                  :class="{ 'is-draft': !w.published }"
                  aria-hidden="true"
                >
                  <i :style="{ width: `${percentFilled(w)}%` }"></i>
                </span>
                <span class="week-facts">
                  <template v-if="w.shifts">
                    <span
                      ><b>{{ w.filled }} of {{ w.slots }}</b> slots filled</span
                    >
                    <span
                      ><b>{{ w.shifts }}</b>
                      {{ w.shifts === 1 ? "shift" : "shifts" }}</span
                    >
                    <span>
                      <b>{{ w.available }} of {{ balances.length }}</b> available
                    </span>
                  </template>
                  <span v-else>Nothing planned this week</span>
                </span>
              </span>
              <span class="week-end">
                <span class="pill" :class="pill(w).cls">{{ pill(w).text }}</span>
              </span>
            </RouterLink>
          </div>
        </div>

        <aside class="side">
          <section>
            <h2 class="section-title">Next four weeks</h2>
            <div class="panel">
              <div class="stat-row">
                <span>Slots filled</span><b>{{ totals.filled }} / {{ totals.slots }}</b>
              </div>
              <div class="stat-row">
                <span>Weeks published</span
                ><b>{{ totals.published }} / {{ weeks.length }}</b>
              </div>
              <div class="stat-row">
                <span>People to check in</span><b>{{ waiting }}</b>
              </div>
            </div>
          </section>

          <section v-if="lowest.length">
            <h2 class="section-title">First in line</h2>
            <p class="side-note">Fewest points go first when you fill the next slots.</p>
            <ul class="next-pills">
              <li v-for="m in lowest" :key="m.member_id">
                <span class="np-name">{{ m.name }}</span>
                <span class="np-pts">{{ points(m.balance, { short: true }) }}</span>
              </li>
            </ul>
          </section>
        </aside>
      </div>
    </template>
  </main>
</template>

<style scoped>
* {
  transition: all 0.25s ease-in-out;
}

.overview {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 32px;
  align-items: start;
}

/* Needs you: the right edge takes the colour of the card's button */
.needs {
  display: grid;
  gap: 12px;
  margin-bottom: 32px;
}
.need {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: var(--surface);
  border-radius: var(--r);
  border-right: 3px solid var(--navy);
  box-shadow: var(--shadow);
}
.need.go {
  border-right-color: var(--go);
}
.need-text {
  flex: 1;
  min-width: 0;
}
.need-text strong {
  display: block;
}
.need-text span {
  font-size: 14px;
  color: var(--muted);
}
.need .btn {
  flex: none;
  min-width: 112px;
}
.all-clear {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: var(--r);
  border: 1.5px dashed color-mix(in srgb, var(--green) 55%, transparent);
  background: color-mix(in srgb, var(--mint-surface) 60%, var(--surface));
}
.all-clear strong {
  display: block;
}
.all-clear span {
  font-size: 14px;
  color: var(--muted);
}
.all-clear-icon {
  flex: none;
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--green);
  color: #053b2a;
  font-weight: 800;
}

/* Week rows: green when full, blue with empty slots, grey when not published */
.weeks {
  display: grid;
  gap: 12px;
}
.week {
  display: grid;
  grid-template-columns: 150px minmax(0, 1fr) auto;
  align-items: center;
  gap: 20px;
  padding: 16px 20px;
  background: var(--surface);
  border-radius: var(--r);
  border-right: 3px solid var(--sky);
  box-shadow: var(--shadow);
  color: inherit;
  text-decoration: none;
}
.week:hover {
  box-shadow: 0 6px 18px -6px rgba(8, 72, 135, 0.35);
}
.week.full {
  border-right-color: var(--green);
}
.week.unpublished,
.week.no-shifts {
  border-right-color: color-mix(in srgb, var(--muted) 40%, transparent);
}
.week-name {
  display: block;
  font-weight: 700;
  color: var(--heading);
}
.week-dates {
  font-family: var(--font-time);
  font-size: 13px;
  color: var(--muted);
}
.week-mid {
  display: grid;
  gap: 6px;
  min-width: 0;
}
.meter {
  display: flex;
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--line);
}
.meter i {
  display: block;
  height: 100%;
  background: var(--green);
}
.meter.is-draft i {
  background: var(--sky);
}
.week-facts {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: var(--muted);
}
.week-facts b {
  font-weight: 600;
  color: var(--ink);
}

/* Side column */
.side {
  display: grid;
  gap: 32px;
}
.panel {
  padding: 12px 20px;
  background: var(--surface);
  border-radius: var(--r);
  box-shadow: var(--shadow);
}
.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--line);
  font-size: 14px;
}
.stat-row:last-child {
  border-bottom: 0;
}
.stat-row b {
  font-variant-numeric: tabular-nums;
  color: var(--navy);
}
.side-note {
  margin: -4px 0 12px;
  font-size: 13px;
  color: var(--muted);
}
.next-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.next-pills li {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  padding: 6px 12px;
  background: var(--surface);
  border-radius: 999px;
  box-shadow: var(--shadow);
}
.np-name {
  font-size: 14px;
  font-weight: 600;
}
.np-pts {
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  color: var(--muted);
}

@media (max-width: 900px) {
  .overview {
    grid-template-columns: 1fr;
  }
  .week {
    grid-template-columns: 1fr;
    gap: 10px;
  }
}
</style>
