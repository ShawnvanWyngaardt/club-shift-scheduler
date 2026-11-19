<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  ApiError,
  coordinatorApi,
  type AssignmentDetail,
  type ShiftDetail,
  type ShiftTypeInfo,
} from '@/api'
import { useNotice } from '@/composables/useNotice'
import { points } from '@/format'
import {
  formFor,
  timeChanged,
  typeGroups,
  WEIGHT_LABELS,
  type ShiftForm,
  type TypeGroup,
} from '@/shifts'
import { amsterdamToIso, formatDay, formatTimeRange } from '@/time'

const props = defineProps<{ clubId: string; token: string }>()
const emit = defineEmits<{ count: [types: number] }>()
const clubId = computed(() => Number(props.clubId))
const { showNotice } = useNotice()

const types = ref<ShiftTypeInfo[]>([])
const shifts = ref<ShiftDetail[]>([])
const assignments = ref<AssignmentDetail[]>([])
const state = ref<'loading' | 'ready' | 'error'>('loading')

const errorText = (e: unknown) =>
  e instanceof ApiError ? e.message : 'Could not reach the server.'

async function load() {
  try {
    const [allTypes, allShifts, allAssignments] = await Promise.all([
      coordinatorApi.shiftTypes(clubId.value),
      coordinatorApi.shifts(clubId.value),
      coordinatorApi.assignments(clubId.value, props.token),
    ])
    types.value = allTypes
    shifts.value = allShifts
    assignments.value = allAssignments
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

const groups = computed(() => typeGroups(types.value, shifts.value, assignments.value))
watch(
  () => types.value.length,
  (n) => emit('count', n),
)

/* ---------- New shift type ---------- */
const newType = ref({ name: '', weight: 1 })
const addingType = ref(false)
const typeError = ref('')

async function addType() {
  const name = newType.value.name.trim()
  if (!name) return
  addingType.value = true
  typeError.value = ''
  try {
    const created = await coordinatorApi.addShiftType(
      clubId.value,
      props.token,
      name,
      newType.value.weight,
    )
    newType.value = { name: '', weight: 1 }
    await load()
    openAdd(created.id) // the next step is its first shifts
    showNotice(`${created.name} added.`, 'Now add its first shifts.')
  } catch (e) {
    typeError.value = errorText(e)
  } finally {
    addingType.value = false
  }
}

/* ---------- Edit a shift type ---------- */
const editingType = ref<number | null>(null)
const typeForm = ref({ name: '', weight: 1 })
const typeBusy = ref(false)
const typeRowError = ref<{ id: number; text: string } | null>(null)

function editType(group: TypeGroup) {
  closeForms()
  editingType.value = group.type.id
  typeForm.value = { name: group.type.name, weight: group.type.weight }
}

async function saveType(group: TypeGroup) {
  typeBusy.value = true
  typeRowError.value = null
  const pointsChanged = typeForm.value.weight !== group.type.weight
  try {
    const saved = await coordinatorApi.editShiftType(
      clubId.value,
      props.token,
      group.type.id,
      typeForm.value.name.trim(),
      typeForm.value.weight,
    )
    await load()
    closeForms()
    showNotice(
      `${saved.name} saved.`,
      pointsChanged
        ? `Points already earned stay the same; check-ins from now on earn ${points(saved.weight)}.`
        : undefined,
    )
  } catch (e) {
    typeRowError.value = { id: group.type.id, text: errorText(e) }
  } finally {
    typeBusy.value = false
  }
}

async function removeType(group: TypeGroup) {
  typeBusy.value = true
  typeRowError.value = null
  try {
    await coordinatorApi.remove(clubId.value, props.token, 'shift-types', group.type.id)
    await load()
    closeForms()
    showNotice(`${group.type.name} removed.`)
  } catch (e) {
    typeRowError.value = { id: group.type.id, text: errorText(e) }
  } finally {
    typeBusy.value = false
  }
}

/* ---------- Add shifts under a type ---------- */
const addingFor = ref<number | null>(null)
const addForm = ref({ date: '', start: '09:00', end: '11:00', slots: 2, weeks: 4 })
const adding = ref(false)
const addError = ref('')

function openAdd(typeId: number) {
  closeForms()
  addingFor.value = typeId
}

async function addShifts(group: TypeGroup) {
  const { date, start, end, slots, weeks } = addForm.value
  adding.value = true
  addError.value = ''
  try {
    await coordinatorApi.addWeeklyShifts(clubId.value, props.token, {
      shift_type_id: group.type.id,
      starts_at: amsterdamToIso(date, start),
      ends_at: amsterdamToIso(date, end),
      slots,
      weeks,
    })
    await load()
    closeForms()
    showNotice(
      `${weeks === 1 ? '1 shift' : `${weeks} weekly shifts`} added for ${group.type.name}.`,
      'Members can say if they are available as soon as they open their link.',
    )
  } catch (e) {
    addError.value = errorText(e)
  } finally {
    adding.value = false
  }
}

/* ---------- Edit one shift ---------- */
const editingShift = ref<number | null>(null)
const editForm = ref<ShiftForm>({ date: '', start: '', end: '', slots: 1 })
const original = ref<ShiftForm>({ date: '', start: '', end: '', slots: 1 })
const shiftBusy = ref(false)
const shiftError = ref('')

function editShift(shift: ShiftDetail) {
  closeForms()
  editingShift.value = shift.id
  original.value = formFor(shift)
  editForm.value = { ...original.value }
}

const moved = computed(() => timeChanged(original.value, editForm.value))

async function saveShift(shift: ShiftDetail) {
  const { date, start, end, slots } = editForm.value
  shiftBusy.value = true
  shiftError.value = ''
  const wasMoved = moved.value
  try {
    await coordinatorApi.editShift(clubId.value, props.token, shift.id, {
      starts_at: amsterdamToIso(date, start),
      ends_at: amsterdamToIso(date, end),
      slots,
    })
    await load()
    closeForms()
    showNotice(
      `${shift.shift_type} saved.`,
      wasMoved ? 'Anyone who was available for the old time needs to tick it again.' : undefined,
    )
  } catch (e) {
    shiftError.value = errorText(e)
  } finally {
    shiftBusy.value = false
  }
}

async function removeShift(shift: ShiftDetail) {
  shiftBusy.value = true
  shiftError.value = ''
  try {
    await coordinatorApi.remove(clubId.value, props.token, 'shifts', shift.id)
    await load()
    closeForms()
    showNotice(`${shift.shift_type} on ${formatDay(shift.starts_at)} removed.`)
  } catch (e) {
    shiftError.value = errorText(e)
  } finally {
    shiftBusy.value = false
  }
}

/** One form open at a time, so the page never has two half-finished edits. */
function closeForms() {
  editingType.value = null
  addingFor.value = null
  editingShift.value = null
  typeRowError.value = null
  addError.value = ''
  shiftError.value = ''
}

const validTimes = (form: { date: string; start: string; end: string }) =>
  form.date !== '' && form.end > form.start

onMounted(load)
</script>

<template>
  <p class="fair-note">
    A shift type is the kind of work and what it's worth. Points belong to the type, so every shift
    of that type is worth the same, and the less popular it is, the more it should be worth. Add the
    dates and times with Add shift under each type.
  </p>

  <form class="add" @submit.prevent="addType">
    <input
      v-model="newType.name"
      type="text"
      maxlength="100"
      placeholder="New kind of shift, for example Kit wash"
      aria-label="Name of a new shift type"
    />
    <select v-model.number="newType.weight" aria-label="Points for this shift type">
      <option v-for="w in [1, 2, 3]" :key="w" :value="w">
        {{ points(w) }}: {{ WEIGHT_LABELS[w] }}
      </option>
    </select>
    <button
      type="submit"
      class="btn btn-secondary"
      :disabled="addingType || !newType.name.trim()"
    >
      {{ addingType ? 'Adding…' : 'Add shift type' }}
    </button>
  </form>
  <p v-if="typeError" class="error" role="alert">{{ typeError }}</p>

  <p v-if="state === 'loading'" class="muted">Loading shifts…</p>
  <div v-else-if="state === 'error'">
    <p class="error">Couldn't load your shifts.</p>
    <button type="button" class="btn btn-primary" @click="load">Try again</button>
  </div>
  <p v-else-if="groups.length === 0" class="note">
    No shift types yet. Start with the kinds of work your club needs, such as Bar or Kit wash.
  </p>

  <section v-for="g in groups" :key="g.type.id" class="type-group">
    <div class="type-head">
      <div>
        <h2>{{ g.type.name }}</h2>
        <span class="muted">
          {{ points(g.type.weight) }} when done | {{ g.upcoming.length }} upcoming
        </span>
      </div>
      <div class="btn-row">
        <button
          type="button"
          class="btn btn-small btn-ghost"
          :aria-expanded="editingType === g.type.id"
          @click="editingType === g.type.id ? closeForms() : editType(g)"
        >
          Edit type
        </button>
        <button
          type="button"
          class="btn btn-small btn-secondary"
          :aria-expanded="addingFor === g.type.id"
          @click="addingFor === g.type.id ? closeForms() : openAdd(g.type.id)"
        >
          Add shift
        </button>
      </div>
    </div>

    <!-- Edit the type: name and points -->
    <form v-if="editingType === g.type.id" class="shift-form" @submit.prevent="saveType(g)">
      <label>
        Name
        <input v-model="typeForm.name" type="text" maxlength="100" required />
      </label>
      <label>
        Points
        <select v-model.number="typeForm.weight">
          <option v-for="w in [1, 2, 3]" :key="w" :value="w">
            {{ points(w) }}: {{ WEIGHT_LABELS[w] }}
          </option>
        </select>
      </label>
      <div class="sf-actions">
        <button
          type="submit"
          class="btn btn-small btn-primary"
          :disabled="typeBusy || !typeForm.name.trim()"
        >
          Save
        </button>
        <button type="button" class="btn btn-small btn-ghost" @click="closeForms">Cancel</button>
        <button
          v-if="g.total === 0"
          type="button"
          class="btn btn-small btn-edit"
          :disabled="typeBusy"
          @click="removeType(g)"
        >
          Remove type
        </button>
      </div>
      <p class="note sf-note">
        Points already earned stay as they are. Check-ins from now on use the new points.
      </p>
      <p v-if="typeRowError?.id === g.type.id" class="error sf-note" role="alert">
        {{ typeRowError.text }}
      </p>
    </form>

    <!-- Add shifts of this type -->
    <form v-if="addingFor === g.type.id" class="shift-form" @submit.prevent="addShifts(g)">
      <label>First date<input v-model="addForm.date" type="date" required /></label>
      <label>Starts<input v-model="addForm.start" type="time" required /></label>
      <label>Ends<input v-model="addForm.end" type="time" required /></label>
      <label>
        People needed
        <input v-model.number="addForm.slots" type="number" min="1" max="50" />
      </label>
      <label>
        Repeat for weeks
        <input v-model.number="addForm.weeks" type="number" min="1" max="26" />
      </label>
      <div class="sf-actions">
        <button
          type="submit"
          class="btn btn-small btn-primary"
          :disabled="adding || !validTimes(addForm)"
        >
          {{ adding ? 'Adding…' : 'Add shifts' }}
        </button>
        <button type="button" class="btn btn-small btn-ghost" @click="closeForms">Cancel</button>
      </div>
      <p class="note sf-note">
        Weekly: the same day and time, every week for the number of weeks you choose. Use 1 for a
        single shift. {{ g.type.name }} is worth {{ points(g.type.weight) }}.
      </p>
      <p v-if="addForm.date && addForm.end <= addForm.start" class="error sf-note">
        The end time must be after the start time.
      </p>
      <p v-if="addError" class="error sf-note" role="alert">{{ addError }}</p>
    </form>

    <div class="rows">
      <template v-for="r in g.upcoming" :key="r.shift.id">
        <div v-if="editingShift !== r.shift.id" class="row">
          <strong>{{ formatDay(r.shift.starts_at) }}</strong>
          <span class="muted">
            <span class="t">{{ formatTimeRange(r.shift.starts_at, r.shift.ends_at) }}</span>
            | {{ r.shift.slots }} {{ r.shift.slots === 1 ? 'person' : 'people' }} |
            {{ r.taken }} on it
          </span>
          <button type="button" class="btn btn-small btn-edit" @click="editShift(r.shift)">
            <svg class="pencil" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
              <path d="M10.9 2.6a1.5 1.5 0 0 1 2.1 0l.4.4a1.5 1.5 0 0 1 0 2.1L6 12.5l-3 .7.7-3z" />
              <path d="M9.5 4l2.5 2.5" />
            </svg>
            Edit<span class="sr-only"> {{ formatDay(r.shift.starts_at) }}</span>
          </button>
        </div>

        <!-- Edit one shift. Once people are on it, only "people needed" can change. -->
        <form v-else class="shift-form editing" @submit.prevent="saveShift(r.shift)">
          <label>
            Date
            <input v-model="editForm.date" type="date" required :disabled="r.taken > 0" />
          </label>
          <label>
            Starts
            <input v-model="editForm.start" type="time" required :disabled="r.taken > 0" />
          </label>
          <label>
            Ends
            <input v-model="editForm.end" type="time" required :disabled="r.taken > 0" />
          </label>
          <label>
            People needed
            <input
              v-model.number="editForm.slots"
              type="number"
              :min="Math.max(1, r.taken)"
              max="50"
            />
          </label>
          <div class="sf-actions">
            <button
              type="submit"
              class="btn btn-small btn-primary"
              :disabled="shiftBusy || !validTimes(editForm) || editForm.slots < r.taken"
            >
              Save
            </button>
            <button type="button" class="btn btn-small btn-ghost" @click="closeForms">
              Cancel
            </button>
            <button
              v-if="r.taken === 0"
              type="button"
              class="btn btn-small btn-edit"
              :disabled="shiftBusy"
              @click="removeShift(r.shift)"
            >
              Remove shift
            </button>
          </div>
          <p v-if="r.taken > 0" class="note sf-note">
            {{ r.taken }} {{ r.taken === 1 ? 'person is' : 'people are' }} on this shift, so its
            time is fixed. To move it, take them off on its week page first.
          </p>
          <p v-else-if="moved" class="note sf-note">
            Anyone who was available for the old time will need to tick it again.
          </p>
          <p v-if="shiftError" class="error sf-note" role="alert">{{ shiftError }}</p>
        </form>
      </template>
      <p v-if="g.upcoming.length === 0" class="note">No upcoming shifts of this type.</p>
    </div>
  </section>
</template>

<style scoped>
.fair-note {
  margin: 0 0 16px;
  font-size: 14px;
  color: var(--muted);
}
.muted {
  color: var(--muted);
}
.note {
  margin: 0;
  font-size: 13px;
  color: var(--muted);
}
.error {
  margin: 8px 0 0;
  font-size: 13px;
}

/* New shift type: name, points, button in one line */
.add {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 28px;
}
.add input,
.add select,
.shift-form input,
.shift-form select {
  min-height: 40px;
  padding: 0 12px;
  border: 1.5px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
  color: var(--ink);
  font: inherit;
  font-size: 14px;
}
.add input {
  flex: 1;
  min-width: 200px;
}
/* Our own chevron, so it can sit 12px in from the edge */
.add select,
.shift-form select {
  padding-right: 40px;
  appearance: none;
  background: var(--surface)
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' width='16' height='16'%3E%3Cpath d='M4 6l4 4 4-4' fill='none' stroke='%23626E78' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E")
    no-repeat right 12px center / 16px 16px;
  cursor: pointer;
}
.shift-form input,
.shift-form select {
  box-sizing: border-box; /* padding inside the width, so fields fit their column */
  width: 100%;
  min-width: 0; /* date and time inputs won't shrink to their column otherwise */
}
.shift-form input:disabled {
  background: var(--bg);
  color: var(--muted);
}

.type-group {
  margin-bottom: 28px;
}
.type-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}
.type-head h2 {
  margin: 0;
  font-size: 16px;
}
.type-head .muted {
  font-size: 13px;
}

/* The forms open under the type, in a card with a sky edge */
.shift-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  align-items: end;
  gap: 12px;
  margin-bottom: 12px;
  padding: 16px;
  background: var(--surface);
  border-radius: var(--r);
  border-right: 3px solid var(--sky);
  box-shadow: var(--shadow);
}
.shift-form.editing {
  margin-bottom: 0;
}
.shift-form label {
  display: grid;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
}
.sf-actions {
  grid-column: 1 / -1; /* their own row, under the fields */
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.sf-note {
  grid-column: 1 / -1;
}

.rows {
  display: grid;
  gap: 8px;
}
.row {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--surface);
  border-radius: var(--r);
  box-shadow: var(--shadow);
}
.row .muted {
  font-size: 13px;
}
.row .t {
  font-family: var(--font-time);
}
.pencil {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linejoin: round;
}

@media (max-width: 600px) {
  .row {
    grid-template-columns: minmax(0, 1fr) auto;
  }
  .row .muted {
    grid-column: 1;
    grid-row: 2;
  }
  .row .btn {
    grid-row: 1 / span 2;
    grid-column: 2;
  }
}
</style>
