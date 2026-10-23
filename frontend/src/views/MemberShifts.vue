<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api, ApiError, type MemberProfile, type MyShift } from '@/api'
import { formatDay, formatTimeRange } from '@/time'

const props = defineProps<{ token: string }>()

const profile = ref<MemberProfile | null>(null)
const shifts = ref<MyShift[]>([])
const selected = ref(new Set<number>())
const pageState = ref<'loading' | 'ready' | 'invalid' | 'error'>('loading')
const saveState = ref<'idle' | 'saving' | 'saved' | 'failed'>('idle')
const saveMessage = ref('')

function applyShifts(list: MyShift[]) {
  shifts.value = list
  selected.value = new Set(list.filter((s) => s.available || s.assigned).map((s) => s.id))
}

async function load() {
  pageState.value = 'loading'
  try {
    const [me, mine] = await Promise.all([api.me(props.token), api.myShifts(props.token)])
    profile.value = me
    applyShifts(mine)
    pageState.value = 'ready'
  } catch (error) {
    pageState.value = error instanceof ApiError && error.status === 404 ? 'invalid' : 'error'
  }
}

function toggle(shift: MyShift) {
  if (shift.assigned) return
  const next = new Set(selected.value)
  if (next.has(shift.id)) {
    next.delete(shift.id)
  } else {
    next.add(shift.id)
  }
  selected.value = next
  saveState.value = 'idle'
}

async function save() {
  saveState.value = 'saving'
  try {
    applyShifts(await api.saveAvailability(props.token, [...selected.value]))
    saveState.value = 'saved'
  } catch (error) {
    // The ticks stay as they are, so nothing is lost on a bad connection.
    saveMessage.value = error instanceof ApiError ? error.message : 'Could not reach the server.'
    saveState.value = 'failed'
  }
}

const days = computed(() => {
  const groups = new Map<string, MyShift[]>()
  for (const shift of shifts.value) {
    const day = formatDay(shift.starts_at)
    groups.set(day, [...(groups.get(day) ?? []), shift])
  }
  return [...groups].map(([day, items]) => ({ day, items }))
})

onMounted(load)
</script>

<template>
  <main class="page">
    <p v-if="pageState === 'loading'" class="muted">Loading your shifts…</p>

    <section v-else-if="pageState === 'invalid'">
      <h1>This link doesn't work</h1>
      <p class="muted">Ask your club's coordinator to send you a new one.</p>
    </section>

    <section v-else-if="pageState === 'error'">
      <h1>Something went wrong</h1>
      <p class="muted">We couldn't load your shifts.</p>
      <button type="button" @click="load">Try again</button>
    </section>

    <template v-else-if="profile">
      <header class="header">
        <p class="muted">{{ profile.club_name }}</p>
        <h1>Hi {{ profile.name }}</h1>
        <p>
          <strong>{{ profile.balance }} points</strong> this season. Fewer points means you're first
          in line for the next shift.
        </p>
      </header>

      <p v-if="shifts.length === 0" class="muted">
        No upcoming shifts yet. Check back after your coordinator adds some.
      </p>

      <form v-else @submit.prevent="save">
        <fieldset v-for="group in days" :key="group.day" class="day">
          <legend>{{ group.day }}</legend>
          <label
            v-for="shift in group.items"
            :key="shift.id"
            class="shift"
            :class="{ assigned: shift.assigned }"
          >
            <input
              type="checkbox"
              :checked="selected.has(shift.id)"
              :disabled="shift.assigned"
              @change="toggle(shift)"
            />
            <span class="shift-main">
              <span class="shift-name">{{ shift.shift_type }}</span>
              <span class="muted">{{ formatTimeRange(shift.starts_at, shift.ends_at) }}</span>
            </span>
            <span v-if="shift.assigned" class="tag">Assigned to you</span>
            <span v-else class="points">+{{ shift.weight }} points</span>
          </label>
        </fieldset>

        <div class="actions">
          <button type="submit" :disabled="saveState === 'saving'">
            {{ saveState === 'saving' ? 'Saving…' : 'Save my availability' }}
          </button>
          <p v-if="saveState === 'saved'" class="ok" role="status">
            Saved. You can close this page.
          </p>
          <p v-if="saveState === 'failed'" class="error" role="alert">
            {{ saveMessage }} Your ticks are kept, so try again.
          </p>
        </div>
      </form>
    </template>
  </main>
</template>

<style scoped>
.header {
  margin-bottom: var(--space-6);
}
.day {
  border: 0;
  margin: 0 0 var(--space-6);
  padding: 0;
}
legend {
  font-weight: 600;
  margin-bottom: var(--space-2);
}
.shift {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 56px;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  margin-bottom: var(--space-2);
  cursor: pointer;
}
.shift.assigned {
  background: var(--color-surface);
  cursor: default;
}
.shift input {
  width: 20px;
  height: 20px;
  accent-color: var(--color-accent);
}
.shift-main {
  display: flex;
  flex-direction: column;
  flex: 1;
}
.shift-name {
  font-weight: 600;
}
.points {
  color: var(--color-accent);
  font-weight: 600;
  white-space: nowrap;
}
.tag {
  font-size: 0.875rem;
  color: var(--color-muted);
  white-space: nowrap;
}
.actions {
  position: sticky;
  bottom: 0;
  padding: var(--space-4) 0;
  background: var(--color-bg);
}
.actions button {
  width: 100%;
}
.ok {
  color: var(--color-ok);
}
.error {
  color: var(--color-error);
}
</style>
