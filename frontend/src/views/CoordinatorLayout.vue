<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ApiError, coordinatorApi, type ClubPublic } from '@/api'

const props = defineProps<{ clubId: string; token: string }>()

const club = ref<ClubPublic | null>(null)
const state = ref<'loading' | 'ready' | 'invalid' | 'error'>('loading')

async function load() {
  state.value = 'loading'
  try {
    club.value = await coordinatorApi.checkLink(Number(props.clubId), props.token)
    state.value = 'ready'
  } catch (error) {
    const badLink = error instanceof ApiError && [403, 404, 422].includes(error.status)
    state.value = badLink ? 'invalid' : 'error'
  }
}

onMounted(load)
</script>

<template>
  <p v-if="state === 'loading'" class="page-wide muted">Checking your link…</p>

  <main v-else-if="state === 'invalid'" class="page-wide">
    <h1>This coordinator link doesn't work</h1>
    <p class="muted">Check that you copied the whole link.</p>
  </main>

  <main v-else-if="state === 'error'" class="page-wide">
    <h1>Something went wrong</h1>
    <p class="muted">We couldn't reach the server.</p>
    <button type="button" @click="load">Try again</button>
  </main>

  <template v-else-if="club">
    <header class="bar">
      <div class="bar-inner">
        <div>
          <span class="club-name">{{ club.name }}</span>
          <span class="muted"> · Coordinator</span>
        </div>
        <nav aria-label="Coordinator sections" class="tabs">
          <RouterLink :to="{ name: 'schedule', params: { clubId, token } }">Schedule</RouterLink>
          <RouterLink :to="{ name: 'outcomes', params: { clubId, token } }">Outcomes</RouterLink>
        </nav>
      </div>
    </header>
    <RouterView />
  </template>
</template>

<style scoped>
.bar {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}
.bar-inner {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 var(--space-4);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}
.club-name {
  font-weight: 600;
}
.tabs {
  display: flex;
  gap: var(--space-2);
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
