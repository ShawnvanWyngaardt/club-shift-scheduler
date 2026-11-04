<script setup lang="ts">
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
      error instanceof ApiError ? error.message : 'Could not reach the server. James!!!'
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
  return `${c.name} · ${c.points} points${c.busy ? ' · busy at that time' : ''}`
}
</script>

<template>
  <div class="change">
    <div v-if="mode === 'idle'" class="row-actions">
      <button type="button" class="link-button" @click="startGive">Give to someone else</button>
      <button type="button" class="link-button" @click="mode = 'remove'">Remove</button>
    </div>

    <div v-else-if="mode === 'remove'" class="panel" role="group" aria-label="Remove from shift">
      <p>
        Take <strong>{{ assignment.member_name }}</strong> off this shift? Their "I could do this"
        is cleared too, so a refill won't pick them again. The slot stays open until you fill it.
      </p>
      <div class="row-actions">
        <button type="button" class="button-danger" :disabled="working" @click="remove">
          Remove {{ assignment.member_name }}
        </button>
        <button type="button" class="button-secondary" :disabled="working" @click="reset">
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
        <optgroup v-if="saidYes.length" label="Said they could">
          <option v-for="c in saidYes" :key="c.member_id" :value="c.member_id" :disabled="c.busy">
            {{ label(c) }}
          </option>
        </optgroup>
        <optgroup v-if="others.length" label="Didn't say they could">
          <option v-for="c in others" :key="c.member_id" :value="c.member_id" :disabled="c.busy">
            {{ label(c) }}
          </option>
        </optgroup>
      </select>
      <p class="muted hint">People who said they could come first, fewest points on top.</p>
      <div class="row-actions">
        <button type="submit" :disabled="working || chosen === null">Give shift</button>
        <button type="button" class="button-secondary" :disabled="working" @click="reset">
          Cancel
        </button>
      </div>
    </form>

    <p v-if="message" class="error" role="alert">{{ message }}</p>
  </div>
</template>

<style scoped>
.change {
  margin-top: var(--space-2);
}
.panel {
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
}
.panel p {
  margin: 0 0 var(--space-3);
}
.hint {
  margin: var(--space-2) 0 var(--space-3);
}
</style>
