<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, ApiError, type MemberProfile } from '@/api'
import NotFound from '@/views/NotFound.vue'

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

  <NotFound
    v-else-if="state === 'invalid'"
    hint="This link doesn't work any more. Ask your club's coordinator to send you a new one."
  />

  <main v-else-if="state === 'error'" class="page">
    <h1>Something went wrong</h1>
    <p class="muted">We couldn't reach the server.</p>
    <button type="button" @click="load">Try again</button>
  </main>

  <template v-else-if="profile">
    <header>
      <div class="page head member-header">
        <section class="member-header-content">
          <div class="flex flex-col">
            <h1>{{ profile.name }}</h1>
            <p class="muted club">{{ profile.club_name }}</p>
          </div>
          <div class="flex">
            <span class="member-points">
              {{ profile.balance }}
            </span>
          </div>
        </section>
      </div>
    </header>
    <div class="page tab-head">
      <nav aria-label="Your pages" class="tabs">
        <RouterLink :to="{ name: 'member', params: { token } }">My answers</RouterLink>
        <RouterLink :to="{ name: 'member-assignments', params: { token } }">My shifts</RouterLink>
        <RouterLink :to="{ name: 'member-standings', params: { token } }">Club points</RouterLink>
      </nav>
    </div>
    <RouterView :profile="profile" />
  </template>
</template>

<style scoped>
.member-header {
  background: url('../assets/images/member-header.svg') no-repeat 0 0 / cover;
  height: 140px;
}
.member-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 var(--space-3);
}
.member-header-content h1 {
  color: var(--color-text-light);
  margin: 0;
  font-size: 1.5rem;
  font-weight: 800;
}
.member-points {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  top: 18px;
  padding: var(--space-4);
  background-color: var(--color-accent-secondary);
  border: 6px solid var(--color-text-light);
  color: var(--color-text-light);
  font-size: 28px;
  font-weight: 800;
  border-radius: 50%;
  box-sizing: border-box;
  min-width: 48px;
  aspect-ratio: 1;
  line-height: 0.85;
  flex-shrink: 0;
}
.head {
  padding-bottom: 0;
}
.tab-head {
  padding-top: var(--space-1);
}
.club {
  color: var(--color-text-accent);
  font-size: 0.85rem;
  font-style: italic;
  font-weight: 300;
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
  borderprofiom-color: var(--color-accent);
}
</style>
