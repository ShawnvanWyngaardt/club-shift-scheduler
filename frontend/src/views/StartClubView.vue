<script setup lang="ts">
import { computed, ref } from 'vue'
import { ApiError, coordinatorApi, type ClubWithToken } from '@/api'
import { coordinatorUrl, copyText } from '@/links'

const name = ref('')
const club = ref<ClubWithToken | null>(null)
const creating = ref(false)
const error = ref('')
const copied = ref(false)

const link = computed(() =>
  club.value ? coordinatorUrl(club.value.id, club.value.coordinator_token) : '',
)

async function create() {
  creating.value = true
  error.value = ''
  try {
    club.value = await coordinatorApi.createClub(name.value.trim())
  } catch (e) {
    error.value =
      e instanceof ApiError ? e.message : 'Could not reach the server. Please try again.'
  } finally {
    creating.value = false
  }
}

async function copy() {
  copied.value = await copyText(link.value)
}
</script>

<template>
  <main class="page">
    <template v-if="!club">
      <h1>Start a club</h1>
      <p class="muted">You'll be its coordinator. Members get their own links later.</p>
      <form class="form" @submit.prevent="create">
        <label for="club-name" class="field-label">Club name</label>
        <input id="club-name" v-model="name" type="text" required maxlength="100" />
        <button type="submit" :disabled="creating || !name.trim()">
          {{ creating ? 'Creating…' : 'Create club' }}
        </button>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
      </form>
    </template>

    <template v-else>
      <h1>{{ club.name }} is ready</h1>
      <section class="save" aria-labelledby="save-title">
        <h2 id="save-title">Save your coordinator link now</h2>
        <p>
          This link is the only way into your club's coordinator screens. There are no accounts and
          no password reset, so we can't send it again.
        </p>
        <label for="coordinator-link" class="field-label">Your coordinator link</label>
        <input
          id="coordinator-link"
          :value="link"
          type="text"
          readonly
          @focus="($event.target as HTMLInputElement).select()"
        />
        <div class="actions">
          <button type="button" @click="copy">{{ copied ? 'Copied' : 'Copy link' }}</button>
          <RouterLink
            class="link-button button-secondary"
            :to="{
              name: 'setup',
              params: { clubId: String(club.id), token: club.coordinator_token },
            }"
          >
            I've saved it, add members
          </RouterLink>
        </div>
      </section>
    </template>
  </main>
</template>

<style scoped>
.form {
  display: grid;
  gap: var(--space-3);
  margin-top: var(--space-6);
}
.form .field-label {
  margin-bottom: 0;
}
.save {
  border: 2px solid var(--color-warning);
  background: var(--color-warning-surface);
  border-radius: var(--radius);
  padding: var(--space-4);
  margin-top: var(--space-4);
}
.save h2 {
  font-size: 1.125rem;
  margin: 0 0 var(--space-2);
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-3);
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
  margin: 0;
}
</style>
