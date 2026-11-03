<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, ApiError, type MemberProfile } from '@/api'

const props = defineProps<{ token: string }>()

const profile = ref<MemberProfile | null>(null)
const state = ref<'loading' | 'ready' | 'invalid' | 'error'>('loading')

async function load() {
  state.value = 'loading'
  try {
    profile.value = await api.me(props.token)
    state.value = 'ready'
  } catch (error) {
    state.value = error instanceof ApiError && error.status === 404 ? 'invalid' : 'error'
  }
}

onMounted(load)
</script>

<template>
  <main v-if="state === 'loading'" class="page">
    <p class="muted">Loading…</p>
  </main>

  <main v-else-if="state === 'invalid'" class="page">
    <h1>This link doesn't work</h1>
    <p class="muted">Ask your club's coordinator to send you a new one.</p>
  </main>

  <main v-else-if="state === 'error'" class="page">
    <h1>Something went wrong</h1>
    <p class="muted">We couldn't reach the server.</p>
    <button type="button" @click="load">Try again</button>
  </main>

  <template v-else-if="profile">
    <header class="member-header">
      <div class="page head">
        <p class="muted club">{{ profile.club_name }}</p>
        <h1>Hi {{ profile.name }}</h1>
        <p>
          <strong>{{ profile.balance }} points</strong> this season. Fewer points means you're first
          in line for the next shift.
        </p>
        <nav aria-label="Your pages" class="tabs">
          <RouterLink :to="{ name: 'member', params: { token } }">My answers</RouterLink>
          <RouterLink :to="{ name: 'member-assignments', params: { token } }">My shifts</RouterLink>
          <RouterLink :to="{ name: 'member-standings', params: { token } }">Club points</RouterLink>
        </nav>
      </div>
    </header>
    <RouterView :profile="profile" />
  </template>
</template>

<style scoped>
.member-header {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}
.head {
  padding-bottom: 0;
}
.club {
  margin: 0;
}
.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
}
.tabs a {
  display: inline-flex;
  align-items: center;
  min-height: 48px;
  padding: 0 var(--space-3);
  color: var(--color-muted);
  text-decoration: none;
  border-bottom: 3px solid transparent;
}
.tabs a.router-link-exact-active {
  color: var(--color-ink);
  font-weight: 600;
  border-bottom-color: var(--color-accent);
}
</style>
