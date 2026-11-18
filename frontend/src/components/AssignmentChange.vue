<script setup lang="ts">
import { points } from '@/format'
import { computed, ref } from 'vue'
import { ApiError, coordinatorApi, type AssignmentDetail, type Candidate } from '@/api'

const props = defineProps<{ token: string; assignment: AssignmentDetail }>()
const emit = defineEmits<{ changed: [] }>()

const mode = ref<'idle' | 'remove' | 'give'>('idle')
const candidates = ref<Candidate[]>([])
const chosen = ref<number | null>(null)
const working = ref(false)
const message = ref('')

const saidYes = computed(() => candidates.value.filter((c) => c.said_yes))
const others = computed(() => candidates.value.filter((c) => !c.said_yes))

function reset() {
  mode.value = 'idle'
  chosen.value = null
  message.value = ''
}

async function run(action: () => Promise<unknown>, after?: () => void) {
  working.value = true
  message.value = ''
  try {
    await action()
    after?.()
  } catch (error) {
    message.value =
      error instanceof ApiError ? error.message : 'Could not reach the server.'
  } finally {
    working.value = false
  }
}

function startGive() {
  mode.value = 'give'
  run(async () => {
    candidates.value = await coordinatorApi.candidates(props.token, props.assignment.id)
  })
}

function remove() {
  run(
    () => coordinatorApi.unassign(props.token, props.assignment.id),
    () => {
      reset()
      emit('changed')
    },
  )
}

function give() {
  if (chosen.value === null) return
  const memberId = chosen.value
  run(
    () => coordinatorApi.reassign(props.token, props.assignment.id, memberId),
    () => {
      reset()
      emit('changed')
    },
  )
}

function label(c: Candidate) {
  return `${c.name} | ${points(c.points)}${c.busy ? ' | busy at that time' : ''}`
}
</script>

<template>
  <div class="change">
    <div v-if="mode === 'idle'" class="row-actions">
      <button type="button" class="btn btn-small btn-edit" @click="startGive">
        Give to someone else
      </button>
      <button type="button" class="btn btn-small btn-edit" @click="mode = 'remove'">Remove</button>
    </div>

    <div v-else-if="mode === 'remove'" class="panel" role="group" aria-label="Remove from shift">
      <p>
        Take <strong>{{ assignment.member_name }}</strong> off this shift? They're marked not
        available for it too, so filling the slots won't pick them again. The slot stays open until
        you fill it.
      </p>
      <div class="row-actions">
        <button type="button" class="btn btn-small btn-primary" :disabled="working" @click="remove">
          Remove {{ assignment.member_name }}
        </button>
        <button type="button" class="btn btn-small btn-ghost" :disabled="working" @click="reset">
          Keep
        </button>
      </div>
    </div>

    <form v-else class="panel" @submit.prevent="give">
      <label class="field-label" :for="`give-${assignment.id}`">
        Give {{ assignment.shift_type }} to
      </label>
      <p v-if="working && candidates.length === 0" class="muted">Loading members…</p>
      <select v-else :id="`give-${assignment.id}`" v-model="chosen" required>
        <option :value="null" disabled>Choose a member</option>
        <optgroup v-if="saidYes.length" label="Available">
          <option v-for="c in saidYes" :key="c.member_id" :value="c.member_id" :disabled="c.busy">
            {{ label(c) }}
          </option>
        </optgroup>
        <optgroup v-if="others.length" label="Not available">
          <option v-for="c in others" :key="c.member_id" :value="c.member_id" :disabled="c.busy">
            {{ label(c) }}
          </option>
        </optgroup>
      </select>
      <p class="muted hint">Available people come first, fewest points on top.</p>
      <div class="row-actions">
        <button type="submit" class="btn btn-small btn-primary" :disabled="working || chosen === null">
          Give shift
        </button>
        <button type="button" class="btn btn-small btn-ghost" :disabled="working" @click="reset">
          Cancel
        </button>
      </div>
    </form>

    <p v-if="message" class="error" role="alert">{{ message }}</p>
  </div>
</template>

<style scoped>
.row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 8px;
}
.panel {
  display: grid;
  gap: 8px;
  margin-top: 8px;
  padding: 12px;
  border-radius: var(--r);
  background: var(--bg);
}
.panel p {
  margin: 0;
  font-size: 14px;
}
.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
}
.hint {
  font-size: 13px;
}
.error {
  margin: 8px 0 0;
  font-size: 13px;
}
</style>
