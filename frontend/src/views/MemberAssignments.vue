<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api, type LedgerEntry, type MemberProfile, type MyAssignment } from '@/api'
import { formatDay, formatTimeRange } from '@/time'

const props = defineProps<{ token: string; profile?: MemberProfile }>()

const assignments = ref<MyAssignment[]>([])
const history = ref<LedgerEntry[]>([])
const state = ref<'loading' | 'ready' | 'error'>('loading')

async function load() {
  state.value = 'loading'
  try {
    const [mine, ledger] = await Promise.all([
      api.myAssignments(props.token),
      api.ledger(props.token),
    ])
    assignments.value = mine
    history.value = ledger.entries
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

const now = Date.now()
const upcoming = computed(() =>
  assignments.value.filter((a) => new Date(a.starts_at).getTime() > now),
)
const past = computed(() =>
  assignments.value.filter((a) => new Date(a.starts_at).getTime() <= now).reverse(),
)

function outcome(a: MyAssignment) {
  if (a.status === 'done') return { text: `Done · +${a.weight} points`, tone: 'ok' }
  if (a.status === 'no_show') return { text: `No-show · −${a.weight} points`, tone: 'error' }
  return { text: 'Waiting for the coordinator to record it', tone: 'muted' }
}

const signed = (change: number) => (change > 0 ? `+${change}` : `−${Math.abs(change)}`)

onMounted(load)
</script>

<template>
  <main class="page">
    <p v-if="state === 'loading'" class="muted">Loading your shifts…</p>

    <section v-else-if="state === 'error'">
      <p class="error">We couldn't load your shifts.</p>
      <button type="button" @click="load">Try again</button>
    </section>

    <template v-else>
      <section class="mb-8">
        <h2>Coming up</h2>
        <p v-if="upcoming.length === 0" class="muted">
          Nothing assigned yet. Your coordinator publishes the schedule once everyone has
          answered.
        </p>
        <ul v-else class="row-list">
          <li v-for="a in upcoming" :key="a.id" class="stack">
            <div class="line">
              <strong>{{ a.shift_type }}</strong>
              <span class="points">+{{ a.weight }} points when done</span>
            </div>
            <p class="muted">
              {{ formatDay(a.starts_at) }}, {{ formatTimeRange(a.starts_at, a.ends_at) }}
            </p>
            <p class="why">
              <strong>Why you:</strong> you said you could do this shift, and members with
              the fewest points go first.
            </p>
          </li>
        </ul>
      </section>

      <section v-if="past.length" class="mb-6">
        <h2>Past shifts</h2>
        <ul class="row-list">
          <li v-for="a in past" :key="a.id">
            <div>
              <strong>{{ a.shift_type }}</strong>
              <p class="muted">
                {{ formatDay(a.starts_at) }},
                {{ formatTimeRange(a.starts_at, a.ends_at) }}
              </p>
            </div>
            <span :class="outcome(a).tone">{{ outcome(a).text }}</span>
          </li>
        </ul>
      </section>

      <section v-if="history.length" class="mb-6">
        <h2>How you got your points</h2>
        <ul class="row-list">
          <li v-for="(entry, index) in history" :key="index">
            <span>{{ entry.reason }}</span>
            <strong>{{ signed(entry.change) }}</strong>
          </li>
        </ul>
      </section>
    </template>
  </main>
</template>

<style scoped>
.row-list li.stack {
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-1, 4px);
}
.line {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-2);
  width: 100%;
}
.row-list p {
  margin: 0;
}
.points {
  color: var(--color-accent);
  font-weight: 600;
}
.why {
  font-size: 0.9375rem;
}
.ok {
  color: var(--color-ok);
  font-weight: 600;
}
</style>
