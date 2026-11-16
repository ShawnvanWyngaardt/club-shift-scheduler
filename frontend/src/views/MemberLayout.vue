<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
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

/*
 * The sliding tab indicator. One bar for the whole nav, moved under the active
 * tab. This layout stays mounted when the tab changes (only the RouterView
 * swaps), so the bar survives and CSS can animate it from the old tab to the new one.
 */
const route = useRoute()
const tabs = ref<HTMLElement | null>(null)
const bar = ref({ x: 0, y: 0, width: 0 })
const animate = ref(false) // off for the first placement, so it doesn't slide in from the left

function moveBar() {
  const active = tabs.value?.querySelector<HTMLElement>('.router-link-exact-active')
  if (!tabs.value || !active) return
  const nav = tabs.value.getBoundingClientRect()
  const tab = active.getBoundingClientRect()
  bar.value = { x: tab.left - nav.left, y: tab.bottom - nav.top - 4, width: tab.width }
}

// Re-measure when the tab changes, and when the nav appears after loading.
watch([() => route.name, tabs], async () => {
  await nextTick() // wait for the new active class (and its bolder, wider text)
  moveBar()
  requestAnimationFrame(() => (animate.value = true))
})

// Re-measure when the nav changes size: window resize, tabs wrapping, fonts loading.
const resize = new ResizeObserver(moveBar)
watch(tabs, (el, old) => {
  if (old) resize.unobserve(old)
  if (el) resize.observe(el)
})
onBeforeUnmount(() => resize.disconnect())
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
            <p class="club">{{ profile.club_name }}</p>
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
      <nav ref="tabs" aria-label="Your pages" class="tabs">
        <span
          class="tab-bar"
          :class="{ animate }"
          :style="{
            width: `${bar.width}px`,
            transform: `translate(${bar.x}px, ${bar.y}px)`,
          }"
          aria-hidden="true"
        ></span>
        <div>
          <RouterLink :to="{ name: 'member', params: { token } }"
            >My availability</RouterLink
          >
          <RouterLink :to="{ name: 'member-assignments', params: { token } }"
            >My shifts</RouterLink
          >
        </div>
        <RouterLink :to="{ name: 'member-standings', params: { token } }"
          >Club points</RouterLink
        >
      </nav>
    </div>
    <RouterView :profile="profile" />
  </template>
</template>

<style scoped>
.member-header {
  background: url("../assets/images/member-header.svg") no-repeat 50% 50% / cover;
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
  border-radius: var(--radius-full-rounded);
  box-sizing: border-box;
  min-width: 48px;
  line-height: 0.75;
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
  position: relative; /* the bar is placed relative to the nav */
  border-bottom: 1px solid var(--color-border-dark);
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
  justify-content: space-between;
}
.tabs a {
  display: inline-flex;
  align-items: center;
  font-size: 0.875rem;
  min-height: 48px;
  padding: 0 var(--space-3);
  color: var(--color-member-dark-1);
  text-decoration: none;
  border-bottom: 4px solid transparent; /* keeps the room the bar sits in */
}
.tabs a.router-link-exact-active {
  font-weight: 700;
}

.tab-bar {
  position: absolute;
  top: 2px;
  left: 0;
  height: 5px;
  background: var(--color-cta-primary-gradient);
  border-radius: var(--radius);
  pointer-events: none;
}
.tab-bar.animate {
  transition: transform 300ms cubic-bezier(0.2, 0.8, 0.2, 1),
    width 300ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
@media (prefers-reduced-motion: reduce) {
  .tab-bar.animate {
    transition: none;
  }
}
</style>
