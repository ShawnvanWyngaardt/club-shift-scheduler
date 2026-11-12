<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api, ApiError, type MemberProfile, type MyShift } from '@/api'
import { formatTimeRange, groupByDay } from '@/time'

const props = defineProps<{ token: string; profile?: MemberProfile }>()

const shifts = ref<MyShift[]>([])
const selected = ref(new Set<number>())
const state = ref<'loading' | 'ready' | 'error'>('loading')
const saveState = ref<'idle' | 'saving' | 'saved' | 'failed'>('idle')
const saveMessage = ref('')

function applyShifts(list: MyShift[]) {
  shifts.value = list
  selected.value = new Set(list.filter((s) => s.available || s.assigned).map((s) => s.id))
}

async function load() {
  state.value = 'loading'
  try {
    applyShifts(await api.myShifts(props.token))
    state.value = 'ready'
  } catch {
    state.value = 'error'
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

const days = computed(() => groupByDay(shifts.value))
const ticked = computed(() => shifts.value.filter((s) => selected.value.has(s.id)).length)

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
      <section class="explain">
        <h2>Which shifts could you do?</h2>
        <p class="descriptive">
          Tick every upcoming shift you could help with, then Save. This indicates your
          availability, and is NOT a final schedule.
        </p>
        <p class="descriptive">
          The club coordinator's scheduler decides who gets assigned, and members with the
          fewest points get picked first to better their scoring chances.
        </p>
      </section>

      <p v-if="shifts.length === 0" class="descriptive">
        No upcoming shifts yet. Check back after your coordinator adds new shifts.
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
              <span class="shift-time">{{
                formatTimeRange(shift.starts_at, shift.ends_at)
              }}</span>
            </span>
            <span v-if="shift.assigned" class="tag"
              >Yours · +{{ shift.weight }} points</span
            >
            <span v-else class="points">+{{ shift.weight }} points</span>
          </label>
        </fieldset>

        <div class="actions">
          <p class="count">Available for {{ ticked }} of {{ shifts.length }} shifts.</p>
          <button type="submit" class="btn-cta" :disabled="saveState === 'saving'">
            {{ saveState === "saving" ? "Saving…" : "Save my availability" }}
          </button>
          <span v-if="saveState === 'saved'" role="status">
            Your availability has been saved.<br />You can update it when necessary but
            remember to save again.
          </span>
          <span v-if="saveState === 'failed'" role="alert">
            {{ saveMessage }} Your selections are kept, so please try again.
          </span>
        </div>
      </form>
    </template>
  </main>
</template>

<style scoped>
.explain {
  margin-bottom: var(--space-6);
}

.descriptive {
  color: var(--color-text);
  font-size: 1rem;
  line-height: 1.5;
}

.day {
  border: 0;
  margin: 0 0 var(--space-6);
  padding: 0;
}

fieldset {
  margin: 0 0 var(--space-6);
}

legend {
  color: var(--color-member-dark-1);
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: var(--space-2);
}

.shift {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  min-height: 56px;
  padding: var(--space-3) var(--space-4);
  border-top: none;
  border-right: 3px solid transparent;
  border-bottom: 1px solid transparent;
  border-left: none;
  border-radius: var(--radius);
  box-shadow: 0px 3px 12px -5px var(--color-shadow);
  margin-bottom: var(--space-3);
  cursor: pointer;
}

.shift:has(input:checked) {
  border-color: var(--color-text-accent);
}

.shift.assigned {
  background: var(--color-surface);
  cursor: default;
}

.shift-main {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.shift-name {
  color: var(--color-text);
  font-size: 1rem;
  font-weight: 600;
}

.shift-time {
  font-family: var(--font-time);
  font-size: 0.875rem;
  font-weight: 400;
  color: var(--color-text-muted);
}

.points {
  color: var(--color-text-muted);
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

.actions {
  position: sticky;
  bottom: 0;
  padding: var(--space-7);
  background: var(--color-bg);
  border-top: 3px solid var(--color-member-dark-1);
  text-align: center;
  font-size: 0.875rem;
  line-height: 1.35;
}

.actions button {
  margin: var(--space-6) 0;
  width: 100%;
}

.count {
  background: var(--color-pill-bg-accent);
  border: 1px solid var(--color-text-accent);
  border-radius: var(--radius-rounded);
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
  margin: 0 auto var(--space-2);
  width: fit-content;
  padding: var(--space-1) var(--space-4);
  color: var(--color-text-accent);
}
</style>
