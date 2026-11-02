<script setup lang="ts">
import { ref } from 'vue'
import { ApiError, coordinatorApi, type ShiftTypeInfo } from '@/api'

const props = defineProps<{ clubId: string; token: string; shiftTypes: ShiftTypeInfo[] }>()
const emit = defineEmits<{ changed: [] }>()

const name = ref('')
const weight = ref(1)
const adding = ref(false)
const formError = ref('')
const rowError = ref<{ id: number; text: string } | null>(null)

const weightLabels: Record<number, string> = {
  1: 'Easy to fill',
  2: 'Takes some asking',
  3: 'Nobody wants it',
}

const errorText = (e: unknown) =>
  e instanceof ApiError ? e.message : 'Could not reach the server.'

async function add() {
  adding.value = true
  formError.value = ''
  try {
    await coordinatorApi.addShiftType(
      Number(props.clubId),
      props.token,
      name.value.trim(),
      weight.value,
    )
    name.value = ''
    weight.value = 1
    emit('changed')
  } catch (e) {
    formError.value = errorText(e)
  } finally {
    adding.value = false
  }
}

async function remove(shiftType: ShiftTypeInfo) {
  if (!window.confirm(`Remove the shift type "${shiftType.name}"?`)) return
  rowError.value = null
  try {
    await coordinatorApi.remove(Number(props.clubId), props.token, 'shift-types', shiftType.id)
    emit('changed')
  } catch (e) {
    rowError.value = { id: shiftType.id, text: errorText(e) }
  }
}
</script>

<template>
  <section class="setup-section" aria-labelledby="types-title">
    <h2 id="types-title">2. Shift types</h2>
    <p class="muted">
      The kinds of work your club needs. Unpopular ones are worth more points, so whoever takes them
      gets priority later.
    </p>

    <form class="form-grid" @submit.prevent="add">
      <div>
        <label for="type-name" class="field-label">Name</label>
        <input id="type-name" v-model="name" type="text" required maxlength="100" />
      </div>
      <div>
        <label for="type-weight" class="field-label">Points</label>
        <select id="type-weight" v-model.number="weight">
          <option v-for="w in [1, 2, 3]" :key="w" :value="w">{{ w }}: {{ weightLabels[w] }}</option>
        </select>
      </div>
      <button type="submit" :disabled="adding || !name.trim()">
        {{ adding ? 'Adding…' : 'Add shift type' }}
      </button>
    </form>
    <p v-if="formError" class="error" role="alert">{{ formError }}</p>

    <p v-if="shiftTypes.length === 0" class="muted">No shift types yet.</p>
    <ul v-else class="row-list" aria-label="Shift types">
      <li v-for="shiftType in shiftTypes" :key="shiftType.id">
        <span>
          <strong>{{ shiftType.name }}</strong>
          <span class="muted"> · +{{ shiftType.weight }} points</span>
        </span>
        <button type="button" class="button-danger" @click="remove(shiftType)">Remove</button>
        <p v-if="rowError?.id === shiftType.id" class="error row-error" role="alert">
          {{ rowError?.text }}
        </p>
      </li>
    </ul>
  </section>
</template>
