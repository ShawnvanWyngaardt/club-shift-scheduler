<script setup lang="ts">
import '@/assets/coordinator.css'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ApiError, coordinatorApi, type ClubPublic } from '@/api'
import { waitingForCheckIn } from '@/checkin'
import DemoPanel from '@/components/DemoPanel.vue'
import NoticeBar from '@/components/NoticeBar.vue'
import { useSlidingTabBar } from '@/composables/useSlidingTabBar'
import { recallDemo } from '@/demo'

const props = defineProps<{ clubId: string; token: string }>()

const club = ref<ClubPublic | null>(null)
const state = ref<'loading' | 'ready' | 'invalid' | 'error'>('loading')

// Club ids can be reused after a demo is deleted, so the token has to match too.
// Only this club's own demo shows the guide, never one from an earlier visit.
const demo = computed(() => {
  const remembered = recallDemo(Number(props.clubId))
  return remembered?.coordinator_token === props.token ? remembered : null
})

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

/*
 * The orange count on the Check-in tab. It is a hint, so a failed request
 * shows no count rather than an error. Recounted on every tab change, so it
 * catches up after a check-in is saved.
 */
const waiting = ref(0)
async function countWaiting() {
  try {
    const assignments = await coordinatorApi.assignments(Number(props.clubId), props.token)
    waiting.value = waitingForCheckIn(assignments)
  } catch {
    waiting.value = 0
  }
}

const route = useRoute()
watch(
  () => route.name,
  () => {
    if (state.value === 'ready') countWaiting()
  },
)

onMounted(async () => {
  await load()
  if (state.value === 'ready') countWaiting()
})

const tabs = ref<HTMLElement | null>(null)
const { barStyle, animate } = useSlidingTabBar(tabs)
</script>

<template>
  <div class="coord">
    <p v-if="state === 'loading'" class="wrap state muted">Checking your link…</p>

    <main v-else-if="state === 'invalid'" class="wrap state">
      <h1>This coordinator link doesn't work</h1>
      <p class="muted">Check that you copied the whole link.</p>
    </main>

    <main v-else-if="state === 'error'" class="wrap state">
      <h1>Something went wrong</h1>
      <p class="muted">We couldn't reach the server.</p>
      <button type="button" class="btn btn-primary" @click="load">Try again</button>
    </main>

    <template v-else-if="club">
      <header class="topbar">
        <div class="wrap topbar-inner">
          <div class="head-row">
            <div class="club">
              <span class="eyebrow">Coordinator</span>
              <span class="club-name">{{ club.name }}</span>
            </div>
            <DemoPanel v-if="demo" :demo="demo" />
          </div>
          <nav ref="tabs" aria-label="Coordinator sections" class="tabs">
            <span class="tab-bar" :class="{ animate }" :style="barStyle" aria-hidden="true"></span>
            <RouterLink class="tab" :to="{ name: 'schedule', params: { clubId, token } }">
              Overview
            </RouterLink>
            <RouterLink class="tab" :to="{ name: 'outcomes', params: { clubId, token } }">
              Check-in
              <template v-if="waiting > 0">
                <span class="count" aria-hidden="true">{{ waiting }}</span>
                <span class="sr-only">, {{ waiting }} waiting</span>
              </template>
            </RouterLink>
            <RouterLink class="tab" :to="{ name: 'setup', params: { clubId, token } }">
              Members &amp; shifts
            </RouterLink>
            <!-- Until PR 4 shows points on Members & shifts; then this tab goes. -->
            <RouterLink class="tab" :to="{ name: 'coordinator-points', params: { clubId, token } }">
              Points
            </RouterLink>
          </nav>
        </div>
      </header>
      <NoticeBar />
      <RouterView />
    </template>
  </div>
</template>

<style scoped>
.state {
  padding-block: 32px;
}
.topbar {
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}
.topbar-inner {
  padding-top: 16px;
}
/* Club name on the left; in a demo, the demo card on the right (below it on a phone) */
.head-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.club {
  display: flex;
  flex-direction: column;
}
.eyebrow {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--sky);
}
.club-name {
  font-size: 22px;
  font-weight: 800;
  color: var(--heading);
}

.tabs {
  position: relative; /* the bar is placed relative to the nav */
  display: flex;
  gap: 4px;
  margin-top: 12px;
  overflow-x: auto;
}
.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px 14px;
  color: var(--ink);
  font-size: 14px;
  text-decoration: none;
  white-space: nowrap;
}
.tab.router-link-exact-active {
  font-weight: 600;
  color: var(--navy);
}
.tab-bar {
  position: absolute;
  top: 0;
  left: 0;
  height: 4px;
  border-radius: 4px 4px 0 0;
  background: var(--sky);
  pointer-events: none;
}
.tab-bar.animate {
  transition:
    transform 300ms cubic-bezier(0.2, 0.8, 0.2, 1),
    width 300ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
@media (prefers-reduced-motion: reduce) {
  .tab-bar.animate {
    transition: none;
  }
}
.count {
  display: inline-grid;
  place-items: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--alert);
  color: #fff;
  font-size: 11px;
  font-weight: 800;
}
</style>
