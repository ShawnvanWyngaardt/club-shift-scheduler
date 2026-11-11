<script setup lang="ts">
import { computed, ref } from 'vue'
import { ApiError, coordinatorApi, type Candidate } from '@/api'

const props = defineProps<{ clubId: number; token: string; shiftId: number; shiftLabel: string }>()
const emit = defineEmits<{ changed: [] }>()

const open = ref(false)
const candidates = ref<Candidate[]>([])
const chosen = ref<number | null>(null)
const working = ref(false)
const message = ref('')

const saidYes = computed(() => candidates.value.filter((c) => c.said_yes))
const others = computed(() => candidates.value.filter((c) => !c.said_yes))

function fail(error: unknown) {
  message.value = error instanceof ApiError ? error.message : 'Could not reach the server.'
}

async function start() {
  open.value = true
  working.value = true
  message.value = ''
  try {
    candidates.value = await coordinatorApi.shiftCandidates(
      props.clubId,
      props.token,
      props.shiftId,
    )
  } catch (error) {
    fail(error)
  } finally {
    working.value = false
  }
}

function cancel() {
  open.value = false
  chosen.value = null
  message.value = ''
}

async function assign() {
  if (chosen.value === null) return
  working.value = true
  message.value = ''
  try {
    await coordinatorApi.assignToShift(props.clubId, props.token, props.shiftId, chosen.value)
    cancel()
    emit('changed')
  } catch (error) {
    fail(error)
  } finally {
    working.value = false
  }
}

const optionText = (c: Candidate) =>
  `${c.name} · ${c.points} pts${c.busy ? ' · busy at that time' : ''}`
</script>

<template>
  <div class="fill">
    <button v-if="!open" type="button" class="link-button" @click="start">Assign someone</button>

    <form v-else class="panel" @submit.prevent="assign">
      <label class="field-label" :for="`fill-${shiftId}`">Assign to {{ shiftLabel }}</label>
      <p v-if="working && candidates.length === 0" class="muted">Loading members…</p>
      <select v-else :id="`fill-${shiftId}`" v-model="chosen" required>
        <option :value="null" disabled>Choose a member</option>
        <optgroup v-if="saidYes.length" label="Said they could">
          <option v-for="c in saidYes" :key="c.member_id" :value="c.member_id" :disabled="c.busy">
            {{ optionText(c) }}
          </option>
        </optgroup>
        <optgroup v-if="others.length" label="Didn't say they could">
          <option v-for="c in others" :key="c.member_id" :value="c.member_id" :disabled="c.busy">
            {{ optionText(c) }}
          </option>
        </optgroup>
      </select>
      <div class="row-actions">
        <button type="submit" :disabled="working || chosen === null">Assign</button>
        <button type="button" class="button-secondary" :disabled="working" @click="cancel">
          Cancel
        </button>
      </div>
    </form>

    <p v-if="message" class="error" role="alert">{{ message }}</p>
  </div>
</template>

<style scoped>
.fill {
  margin-top: var(--space-2);
}
.panel {
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
}
.panel select {
  margin-bottom: var(--space-3);
}
</style>
