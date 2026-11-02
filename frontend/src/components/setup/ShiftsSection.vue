<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ApiError, coordinatorApi, type ShiftDetail, type ShiftTypeInfo } from '@/api'
import { amsterdamToIso, formatTimeRange, groupByDay } from '@/time'

const props = defineProps<{ clubId: string; token: string; shiftTypes: ShiftTypeInfo[] }>()

const shifts = ref<ShiftDetail[]>([])
const state = ref<'loading' | 'ready' | 'error'>('loading')
const form = ref({ typeId: 0, date: '', start: '09:00', end: '11:00', slots: 2, weeks: 4 })
const adding = ref(false)
const formError = ref('')
const rowError = ref<{ id: number; text: string } | null>(null)

const errorText = (e: unknown) =>
  e instanceof ApiError ? e.message : 'Could not reach the server.'

// Keep the type picker on a type that still exists.
watch(
  () => props.shiftTypes,
  (types) => {
    if (!types.some((t) => t.id === form.value.typeId)) form.value.typeId = types[0]?.id ?? 0
  },
  { immediate: true },
)

const timesValid = computed(() => form.value.end > form.value.start)
const canAdd = computed(
  () => form.value.typeId > 0 && form.value.date !== '' && timesValid.value && !adding.value,
)
const addLabel = computed(() =>
  form.value.weeks === 1 ? 'Add shift' : `Add ${form.value.weeks} weekly shifts`,
)
const days = computed(() => groupByDay(shifts.value))

async function load() {
  state.value = 'loading'
  try {
    shifts.value = await coordinatorApi.shifts(Number(props.clubId))
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

async function add() {
  adding.value = true
  formError.value = ''
  const { typeId, date, start, end, slots, weeks } = form.value
  try {
    await coordinatorApi.addWeeklyShifts(Number(props.clubId), props.token, {
      shift_type_id: typeId,
      starts_at: amsterdamToIso(date, start),
      ends_at: amsterdamToIso(date, end),
      slots,
      weeks,
    })
    await load()
  } catch (e) {
    formError.value = errorText(e)
  } finally {
    adding.value = false
  }
}

async function remove(shift: ShiftDetail) {
  if (!window.confirm(`Remove this ${shift.shift_type} shift?`)) return
  rowError.value = null
  try {
    await coordinatorApi.remove(Number(props.clubId), props.token, 'shifts', shift.id)
    shifts.value = shifts.value.filter((s) => s.id !== shift.id)
  } catch (e) {
    rowError.value = { id: shift.id, text: errorText(e) }
  }
}

onMounted(load)
</script>

<template>
  <section class="setup-section" aria-labelledby="shifts-title">
    <h2 id="shifts-title">3. Shifts</h2>
    <p class="muted">When the work happens. Add one shift, or repeat it every week.</p>

    <p v-if="shiftTypes.length === 0" class="muted">Add a shift type first.</p>
    <template v-else>
      <form class="form-grid" @submit.prevent="add">
        <div>
          <label for="shift-type" class="field-label">Shift type</label>
          <select id="shift-type" v-model.number="form.typeId">
            <option v-for="t in shiftTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
        </div>
        <div>
          <label for="shift-date" class="field-label">First date</label>
          <input id="shift-date" v-model="form.date" type="date" required />
        </div>
        <div>
          <label for="shift-start" class="field-label">Starts</label>
          <input id="shift-start" v-model="form.start" type="time" required />
        </div>
        <div>
          <label for="shift-end" class="field-label">Ends</label>
          <input id="shift-end" v-model="form.end" type="time" required />
        </div>
        <div>
          <label for="shift-slots" class="field-label">People needed</label>
          <input id="shift-slots" v-model.number="form.slots" type="number" min="1" max="50" />
        </div>
        <div>
          <label for="shift-weeks" class="field-label">Weeks</label>
          <input id="shift-weeks" v-model.number="form.weeks" type="number" min="1" max="26" />
        </div>
        <button type="submit" :disabled="!canAdd">{{ adding ? 'Adding…' : addLabel }}</button>
      </form>
      <p v-if="!timesValid" class="error">The end time must be after the start time.</p>
      <p v-if="formError" class="error" role="alert">{{ formError }}</p>
    </template>

    <p v-if="state === 'loading'" class="muted">Loading shifts…</p>
    <div v-else-if="state === 'error'">
      <p class="error">Couldn't load your shifts.</p>
      <button type="button" @click="load">Try again</button>
    </div>
    <p v-else-if="shifts.length === 0" class="muted">No shifts yet.</p>

    <template v-else>
      <div v-for="group in days" :key="group.day">
        <h3>{{ group.day }}</h3>
        <ul class="row-list">
          <li v-for="shift in group.items" :key="shift.id">
            <span>
              <strong>{{ shift.shift_type }}</strong>
              <span class="muted">
                · {{ formatTimeRange(shift.starts_at, shift.ends_at) }} · {{ shift.slots }}
                {{ shift.slots === 1 ? 'person' : 'people' }}
              </span>
            </span>
            <button type="button" class="button-danger" @click="remove(shift)">Remove</button>
            <p v-if="rowError?.id === shift.id" class="error row-error" role="alert">
              {{ rowError?.text }}
            </p>
          </li>
        </ul>
      </div>
    </template>
  </section>
</template>
