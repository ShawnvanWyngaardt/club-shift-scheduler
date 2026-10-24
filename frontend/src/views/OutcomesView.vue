<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ApiError, coordinatorApi, type AssignmentDetail } from '@/api'
import { formatTimeRange, groupByDay } from '@/time'

const props = defineProps<{ clubId: string; token: string }>()

const assignments = ref<AssignmentDetail[]>([])
const state = ref<'loading' | 'ready' | 'error'>('loading')
const recording = ref<number | null>(null)
const rowError = ref<{ id: number; text: string } | null>(null)

async function load() {
  state.value = 'loading'
  try {
    assignments.value = await coordinatorApi.assignments(Number(props.clubId))
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

async function record(assignment: AssignmentDetail, status: 'done' | 'no_show') {
  recording.value = assignment.id
  rowError.value = null
  try {
    await coordinatorApi.recordOutcome(assignment.id, status, props.token)
    assignment.status = status
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) await load()
    const text = error instanceof ApiError ? error.message : 'Could not reach the server.'
    rowError.value = { id: assignment.id, text }
  } finally {
    recording.value = null
  }
}

const isUpcoming = (a: AssignmentDetail) => new Date(a.starts_at) > new Date()
const statusLabel = (a: AssignmentDetail) =>
  a.status === 'done' ? `Done, +${a.weight}` : `No-show, −${a.weight}`

const toRecordDays = computed(() =>
  groupByDay(assignments.value.filter((a) => a.status === 'assigned')),
)
const recorded = computed(() => assignments.value.filter((a) => a.status !== 'assigned'))

onMounted(load)
</script>

<template>
  <main class="page-wide">
    <p v-if="state === 'loading'" class="muted">Loading assignments…</p>

    <section v-else-if="state === 'error'">
      <h1>Couldn't load outcomes</h1>
      <button type="button" @click="load">Try again</button>
    </section>

    <template v-else>
      <header class="intro">
        <h1>Outcomes</h1>
        <p class="muted">
          Record who turned up. Each choice writes a points entry and can't be undone.
        </p>
      </header>

      <p v-if="assignments.length === 0" class="muted">
        Nothing to record yet. Publish a schedule first.
      </p>

      <section v-for="group in toRecordDays" :key="group.day" class="day">
        <h2>{{ group.day }}</h2>
        <article v-for="a in group.items" :key="a.id" class="row">
          <div class="who">
            <span class="name">{{ a.member_name }}</span>
            <span class="muted">
              {{ a.shift_type }}, {{ formatTimeRange(a.starts_at, a.ends_at) }}
            </span>
            <span v-if="isUpcoming(a)" class="tag">Upcoming</span>
          </div>
          <div class="row-actions">
            <button type="button" :disabled="recording === a.id" @click="record(a, 'done')">
              Done +{{ a.weight }}
            </button>
            <button
              type="button"
              class="button-secondary"
              :disabled="recording === a.id"
              @click="record(a, 'no_show')"
            >
              No-show −{{ a.weight }}
            </button>
          </div>
          <p v-if="rowError?.id === a.id" class="error" role="alert">{{ rowError?.text }}</p>
        </article>
      </section>

      <section v-if="recorded.length" class="day">
        <h2>Recorded</h2>
        <article v-for="a in recorded" :key="a.id" class="row recorded">
          <div class="who">
            <span class="name">{{ a.member_name }}</span>
            <span class="muted">
              {{ a.shift_type }}, {{ formatTimeRange(a.starts_at, a.ends_at) }}
            </span>
          </div>
          <span class="tag">{{ statusLabel(a) }}</span>
        </article>
      </section>
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
.row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-2);
}
.row.recorded {
  background: var(--color-surface);
}
.who {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-2) var(--space-3);
}
.name {
  font-weight: 600;
}
.row-actions {
  display: flex;
  gap: var(--space-2);
}
.row .error {
  flex-basis: 100%;
  margin: 0;
  color: var(--color-error);
}
</style>
