<script setup lang="ts">
import { points } from '@/format'
import { computed, onMounted, ref } from 'vue'
import { api, type MemberProfile, type MyAssignment } from '@/api'
import { formatDay, formatTimeRange } from '@/time'

const props = defineProps<{ token: string; profile?: MemberProfile }>()

const assignments = ref<MyAssignment[]>([])
const state = ref<'loading' | 'ready' | 'error'>('loading')

async function load() {
  state.value = 'loading'
  try {
    assignments.value = await api.myAssignments(props.token)
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

const now = Date.now()
// Coming up: still to do. A shift leaves it once it has started or has an outcome,
// because a coordinator can record done or no-show before the start time.
const isUpcoming = (a: MyAssignment) =>
  a.status === 'assigned' && new Date(a.starts_at).getTime() > now

const upcoming = computed(() => assignments.value.filter(isUpcoming))
const history = computed(() => assignments.value.filter((a) => !isUpcoming(a)).reverse())

/** What a recorded shift did to the balance. The same rule as the backend. */
function change(a: MyAssignment) {
  if (a.status === 'done') return a.weight
  if (a.status === 'no_show') return -a.weight
  return 0
}

function outcome(a: MyAssignment) {
  if (a.status === 'done') return { label: 'Done', tone: 'ok' }
  if (a.status === 'no_show') return { label: 'Missed', tone: 'missed' }
  return { label: 'Waiting to be recorded', tone: 'waiting' }
}

onMounted(load)
</script>

<template>
  <main class="page">
    <p v-if="state === 'loading'" class="muted">Loading your shifts…</p>

    <section v-else-if="state === 'error'">
      <p class="error">We couldn't load your shifts.</p>
      <button type="button" class="btn-secondary" @click="load">Try again</button>
    </section>

    <template v-else>
      <section class="mb-8">
        <h2>Coming up</h2>

        <div v-if="upcoming.length === 0 && history.length" class="empty">
          <h3>No new shifts for you yet</h3>
          <p class="descriptive">
            When your coordinator adds new shifts, tick the ones you can do in
            <RouterLink :to="{ name: 'member', params: { token } }"
              >My availability</RouterLink
            >. Your next shifts show up here once the schedule is published.
          </p>
        </div>

        <div v-else-if="upcoming.length === 0" class="empty">
          <h3>No shifts for you yet</h3>
          <p class="descriptive">
            Your shifts show up here once your coordinator publishes the schedule.
          </p>

          <h3 class="mt">What happens next</h3>
          <ol class="steps">
            <li>
              You tick the shifts you can do in
              <RouterLink :to="{ name: 'member', params: { token } }"
                >My availability</RouterLink
              >.
            </li>
            <li>Your coordinator shares the shifts out and publishes the schedule.</li>
            <li>Your shifts appear here, with the points each one earns.</li>
          </ol>

          <p class="rule">
            <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
              <circle
                cx="12"
                cy="12"
                r="9.5"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              />
              <path
                d="M12 11v6M12 7.5v.01"
                stroke="currentColor"
                stroke-width="2.4"
                stroke-linecap="round"
              />
            </svg>
            <span>
              Shifts go to members who said they could do them, and those with the fewest
              points go first.
            </span>
          </p>
        </div>

        <template v-else>
          <p class="descriptive mb-8">
            You're on these because you said you could do them, and members with the
            fewest points go first. Each shift shows the points you'll earn once it's
            done.
          </p>
          <ul class="cards">
            <li v-for="a in upcoming" :key="a.id" class="card">
              <span class="card-main">
                <span class="card-name">{{ a.shift_type }}</span>
                <span class="card-time">
                  {{ formatDay(a.starts_at) }},
                  {{ formatTimeRange(a.starts_at, a.ends_at) }}
                </span>
              </span>
              <span class="card-points">{{ points(a.weight, { sign: true }) }}</span>
            </li>
          </ul>
        </template>
      </section>

      <section v-if="history.length" class="mb-6">
        <h2>History</h2>
        <ul class="cards">
          <li v-for="a in history" :key="a.id" class="card" :class="outcome(a).tone">
            <span class="card-main">
              <span class="card-name">{{ a.shift_type }}</span>
              <span class="card-time">
                {{ formatDay(a.starts_at) }},
                {{ formatTimeRange(a.starts_at, a.ends_at) }}
              </span>
            </span>
            <span class="card-result">
              <span class="pill">{{ outcome(a).label }}</span>
              <span v-if="a.status !== 'assigned'" class="card-points">
                {{ points(change(a), { sign: true }) }}
              </span>
            </span>
          </li>
        </ul>
      </section>
    </template>
  </main>
</template>

<style scoped>
/* Cards: the same look as the shifts on My availability */
.cards {
  list-style: none;
  margin: 0;
  padding: 0;
}
.card {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  min-height: 56px;
  padding: var(--space-3) var(--space-4);
  border-right: 3px solid var(--color-text-accent);
  border-bottom: 1px solid transparent;
  border-radius: var(--radius);
  box-shadow: 0px 3px 12px -5px var(--color-shadow);
  margin-bottom: var(--space-3);
}
.card-main {
  display: flex;
  flex-direction: column;
  flex: 1;
}
.card-name {
  color: var(--color-text);
  font-size: 1rem;
  font-weight: 600;
}
.card-time {
  font-family: var(--font-time);
  font-size: 0.875rem;
  color: var(--color-text-muted);
}
.card-points {
  color: var(--color-text-accent);
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}
.card-result {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-1);
}
.pill {
  padding: 2px var(--space-2);
  border-radius: var(--radius-full-rounded);
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

/* History: done stands out in the balance orange, missed steps back in grey */
.card.ok {
  border-color: var(--color-accent-secondary);
}
.card.ok .pill {
  background: var(--color-accent-secondary);
  color: var(--color-text-light);
}
.card.ok .card-points {
  color: var(--color-accent-secondary);
}
.card.missed {
  border-right-color: transparent;
}
.card.missed .card-name,
.card.missed .card-time,
.card.missed .card-points {
  color: var(--color-text-muted);
}
.card.missed .pill {
  background: #909cc226;
  color: var(--color-text-muted);
}
.card.waiting {
  border-right-color: var(--color-border-dark);
}
.card.waiting .pill {
  background: var(--color-pill-bg-accent);
  color: var(--color-member-dark-1);
}

/* Empty states for "Coming up": a dashed outline reads as "a space for shifts" */
.empty {
  padding: var(--space-7);
  border: 1.5px dashed var(--color-border-dark);
  border-radius: var(--radius-rounded);
}
.empty h3 {
  /* Every heading in the box: the same as the day headings on My availability */
  color: var(--color-text);
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 var(--space-2);
}
.empty .descriptive {
  margin: 0;
}
.empty h3.mt {
  margin: var(--space-6) 0 var(--space-3);
}
/* The link: the amber and underline used for links on the landing page */
.empty a {
  color: var(--color-text-accent);
  font-weight: 600;
  text-decoration: underline;
  text-underline-position: from-font;
}
.empty a:hover {
  color: var(--color-accent-secondary);
}
.steps {
  list-style: none;
  counter-reset: step;
  display: grid;
  gap: var(--space-3);
  margin: 0;
  padding: 0;
}
.steps li {
  counter-increment: step;
  display: grid;
  grid-template-columns: 24px 1fr;
  column-gap: var(--space-3);
  color: var(--color-text);
  font-size: 0.875rem;
  line-height: 1.5;
}
.steps li::before {
  content: counter(step);
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  margin-top: -1px;
  border-radius: 50%;
  background: var(--color-accent-secondary); /* the orange of the points badge */
  color: var(--color-text-light);
  font-size: 0.75rem;
  font-weight: 700;
}
.rule {
  display: flex;
  gap: var(--space-3);
  align-items: center;
  margin: var(--space-6) 0 0;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius);
  background: var(--color-dark-gradient); /* the same as an assigned shift */
  color: var(--color-text-light);
  font-size: 0.875rem;
  line-height: 1.5;
}
.rule svg {
  flex: none;
  margin-top: 1px;
  color: var(--color-text-accent); /* decorative, aria-hidden */
}
</style>
