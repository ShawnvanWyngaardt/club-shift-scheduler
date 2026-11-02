<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ApiError, coordinatorApi, type MemberLink } from '@/api'
import { copyText, memberUrl, whatsappUrl } from '@/links'

const props = defineProps<{ clubId: string; token: string }>()

const members = ref<MemberLink[]>([])
const state = ref<'loading' | 'ready' | 'error'>('loading')
const newName = ref('')
const adding = ref(false)
const formError = ref('')
const rowError = ref<{ id: number; text: string } | null>(null)
const copied = ref<number | null>(null)

const errorText = (e: unknown) =>
  e instanceof ApiError ? e.message : 'Could not reach the server.'

async function load() {
  state.value = 'loading'
  try {
    members.value = await coordinatorApi.memberLinks(Number(props.clubId), props.token)
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

async function add() {
  adding.value = true
  formError.value = ''
  try {
    const member = await coordinatorApi.addMember(
      Number(props.clubId),
      props.token,
      newName.value.trim(),
    )
    members.value = [...members.value, member].sort((a, b) => a.name.localeCompare(b.name))
    newName.value = ''
  } catch (e) {
    formError.value = errorText(e)
  } finally {
    adding.value = false
  }
}

async function remove(member: MemberLink) {
  if (!window.confirm(`Remove ${member.name}? Their link will stop working.`)) return
  rowError.value = null
  try {
    await coordinatorApi.remove(Number(props.clubId), props.token, 'members', member.id)
    members.value = members.value.filter((m) => m.id !== member.id)
  } catch (e) {
    rowError.value = { id: member.id, text: errorText(e) }
  }
}

async function copy(member: MemberLink) {
  copied.value = (await copyText(memberUrl(member.access_token))) ? member.id : null
}

const shareText = (member: MemberLink) =>
  `Hi ${member.name}, here's your personal link for picking volunteer shifts. ` +
  `It's yours alone, so please don't forward it: ${memberUrl(member.access_token)}`

onMounted(load)
</script>

<template>
  <section class="setup-section" aria-labelledby="members-title">
    <h2 id="members-title">1. Members</h2>
    <p class="muted">Everyone who helps out. Each member gets a personal link.</p>

    <form class="form-grid" @submit.prevent="add">
      <div>
        <label for="member-name" class="field-label">Member name</label>
        <input id="member-name" v-model="newName" type="text" required maxlength="100" />
      </div>
      <button type="submit" :disabled="adding || !newName.trim()">
        {{ adding ? 'Adding…' : 'Add member' }}
      </button>
    </form>
    <p v-if="formError" class="error" role="alert">{{ formError }}</p>

    <p v-if="state === 'loading'" class="muted">Loading members…</p>
    <div v-else-if="state === 'error'">
      <p class="error">Couldn't load your members.</p>
      <button type="button" @click="load">Try again</button>
    </div>
    <p v-else-if="members.length === 0" class="muted">No members yet.</p>

    <ul v-else class="row-list" aria-label="Members">
      <li v-for="member in members" :key="member.id">
        <strong>{{ member.name }}</strong>
        <div class="row-actions">
          <button type="button" class="button-secondary" @click="copy(member)">
            {{ copied === member.id ? 'Copied' : 'Copy link' }}
          </button>
          <a
            class="link-button button-secondary"
            :href="whatsappUrl(shareText(member))"
            target="_blank"
            rel="noopener"
          >
            Share on WhatsApp
          </a>
          <button type="button" class="button-danger" @click="remove(member)">Remove</button>
        </div>
        <p v-if="rowError?.id === member.id" class="error row-error" role="alert">
          {{ rowError?.text }}
        </p>
      </li>
    </ul>
  </section>
</template>
