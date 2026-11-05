<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { coordinatorApi, type Ledger } from '@/api'
import { formatDay } from '@/time'

const props = defineProps<{ clubId: string; token: string }>()

const ledger = ref<Ledger | null>(null)
const state = ref<'loading' | 'ready' | 'error'>('loading')
const memberFilter = ref<number | 'all'>('all')

async function load() {
  state.value = 'loading'
  try {
    ledger.value = await coordinatorApi.ledger(Number(props.clubId), props.token)
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

// Sorted by points here, unlike the member view: the coordinator needs to see who is next in line.
const balances = computed(() =>
  [...(ledger.value?.balances ?? [])].sort(
    (a, b) => a.balance - b.balance || a.name.localeCompare(b.name),
  ),
)
const names = computed(() => new Map(balances.value.map((b) => [b.member_id, b.name])))
const entries = computed(() =>
  (ledger.value?.entries ?? []).filter(
    (entry) => memberFilter.value === 'all' || entry.member_id === memberFilter.value,
  ),
)

const reasonText = (reason: string) =>
  reason.replace(/^done:/, 'Done:').replace(/^no_show:/, 'No-show:')
const signed = (change: number) => (change > 0 ? `+${change}` : `−${Math.abs(change)}`)

onMounted(load)
</script>

<template>
  <main class="page">
    <p v-if="state === 'loading'" class="muted">Loading points…</p>

    <section v-else-if="state === 'error'">
      <p class="error">We couldn't load the points.</p>
      <button type="button" @click="load">Try again</button>
    </section>

    <template v-else>
      <section class="block">
        <h2>Who is next in line</h2>
        <p class="muted">
          Fewest points go first when you fill the next schedule. Members only see this list
          alphabetically, so it doesn't turn into a leaderboard.
        </p>
        <table class="balances">
          <thead>
            <tr>
              <th scope="col">Member</th>
              <th scope="col" class="num">Points</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in balances" :key="b.member_id">
              <td>{{ b.name }}</td>
              <td class="num">{{ b.balance }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="block">
        <h2>History</h2>
        <p v-if="ledger?.entries.length === 0" class="muted">
          No points yet. Points are added when you record an outcome.
        </p>
        <template v-else>
          <label class="field-label" for="points-filter">Show</label>
          <select id="points-filter" v-model="memberFilter">
            <option value="all">Everyone</option>
            <option v-for="b in balances" :key="b.member_id" :value="b.member_id">
              {{ b.name }}
            </option>
          </select>
          <ul class="row-list history">
            <li v-for="(entry, index) in entries" :key="index">
              <div>
                <strong>{{ names.get(entry.member_id) ?? 'Removed member' }}</strong>
                <p class="muted">
                  {{ reasonText(entry.reason) }} · {{ formatDay(entry.created_at) }}
                </p>
              </div>
              <strong :class="entry.change > 0 ? 'ok' : 'error'">{{ signed(entry.change) }}</strong>
            </li>
          </ul>
        </template>
      </section>
    </template>
  </main>
</template>

<style scoped>
.block {
  margin-bottom: var(--space-6);
}
h2 {
  font-size: 1.25rem;
  margin: 0 0 var(--space-2);
}
.balances {
  width: 100%;
  border-collapse: collapse;
  margin-top: var(--space-3);
}
.balances th,
.balances td {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
}
.balances .num {
  text-align: right;
}
.history {
  margin-top: var(--space-3);
}
.history p {
  margin: 0;
}
.ok {
  color: var(--color-ok);
}
</style>
