<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ApiError, coordinatorApi, type MemberLink } from '@/api'
import { copyText, memberUrl, whatsappUrl } from '@/links'

const props = defineProps<{ clubId: string; token: string }>()

const members = ref<MemberLink[]>([])
const state = ref<'loading' | 'ready' | 'error'>('loading')
const newName = ref('')
const adding = ref(false)
const addError = ref('')
const copied = ref<number | null>(null)

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
  addError.value = ''
  try {
    const member = await coordinatorApi.addMember(
      Number(props.clubId),
      props.token,
      newName.value.trim(),
    )
    members.value = [...members.value, member].sort((a, b) => a.name.localeCompare(b.name))
    newName.value = ''
  } catch (e) {
    addError.value = e instanceof ApiError ? e.message : 'Could not reach the server.'
  } finally {
    adding.value = false
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
  <main class="page-wide">
    <header class="intro">
      <h1>Setup</h1>
      <p class="muted">Add your members, then send each one their personal link.</p>
    </header>

    <form class="add" @submit.prevent="add">
      <label for="member-name" class="field-label">Member name</label>
      <div class="add-row">
        <input id="member-name" v-model="newName" type="text" required maxlength="100" />
        <button type="submit" :disabled="adding || !newName.trim()">
          {{ adding ? 'Adding…' : 'Add member' }}
        </button>
      </div>
      <p v-if="addError" class="error" role="alert">{{ addError }}</p>
    </form>

    <p v-if="state === 'loading'" class="muted">Loading members…</p>
    <section v-else-if="state === 'error'">
      <p class="error">Couldn't load your members.</p>
      <button type="button" @click="load">Try again</button>
    </section>
    <p v-else-if="members.length === 0" class="muted">No members yet. Add the first one above.</p>

    <ul v-else class="members" aria-label="Members">
      <li v-for="member in members" :key="member.id">
        <span class="name">{{ member.name }}</span>
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
        </div>
      </li>
    </ul>
  </main>
</template>

<style scoped>
.intro,
.add {
  margin-bottom: var(--space-6);
}
.add-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.add-row input {
  flex: 1 1 240px;
}
.members {
  list-style: none;
  padding: 0;
  margin: 0;
}
.members li {
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
.name {
  font-weight: 600;
}
.row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.link-button {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 var(--space-4);
  border-radius: var(--radius);
  font-weight: 600;
  text-decoration: none;
}
.error {
  color: var(--color-error);
}
</style>
