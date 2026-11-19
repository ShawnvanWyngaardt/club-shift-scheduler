<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { coordinatorApi } from '@/api'
import MemberList from '@/components/MemberList.vue'
import ShiftList from '@/components/ShiftList.vue'

const props = defineProps<{ clubId: string; token: string }>()

/*
 * Two sections, kept in the URL (?section=shifts), so the Overview's
 * "Add shifts" can open the right one.
 */
const route = useRoute()
const router = useRouter()
const section = computed(() => (route.query.section === 'shifts' ? 'shifts' : 'members'))
function show(next: 'members' | 'shifts') {
  router.replace({ query: next === 'shifts' ? { section: next } : {} })
}

// The counts on the section buttons. Each list updates its own count as it changes.
const memberCount = ref<number | null>(null)
const typeCount = ref<number | null>(null)

async function loadCounts() {
  const id = Number(props.clubId)
  const [links, types] = await Promise.allSettled([
    coordinatorApi.memberLinks(id, props.token),
    coordinatorApi.shiftTypes(id),
  ])
  if (links.status === 'fulfilled') memberCount.value = links.value.length
  if (types.status === 'fulfilled') typeCount.value = types.value.length
}

onMounted(loadCounts)
</script>

<template>
  <main class="wrap">
    <div class="page-head">
      <div>
        <h1>Members &amp; shifts</h1>
        <p class="intro">
          Everything the schedule is built from. <b>Members</b> are the people who help out: each
          one gets a personal link, with no account needed, to tick the shifts they can do.
          <b>Shifts</b> are the work that needs doing, grouped by type, each with the points it
          earns. Set both up here, and the app shares the shifts out fairly from what members tick.
        </p>
      </div>
    </div>

    <div class="subtabs" role="group" aria-label="Section">
      <button type="button" :aria-pressed="section === 'members'" @click="show('members')">
        Members<template v-if="memberCount !== null"
          ><span class="pipe" aria-hidden="true">|</span>{{ memberCount }}</template
        >
      </button>
      <button type="button" :aria-pressed="section === 'shifts'" @click="show('shifts')">
        Shifts<template v-if="typeCount !== null"
          ><span class="pipe" aria-hidden="true">|</span>{{ typeCount }}
          {{ typeCount === 1 ? 'type' : 'types' }}</template
        >
      </button>
    </div>

    <MemberList
      v-if="section === 'members'"
      :club-id="clubId"
      :token="token"
      @count="memberCount = $event"
    />

    <ShiftList v-else :club-id="clubId" :token="token" @count="typeCount = $event" />
  </main>
</template>

<style scoped>
.intro {
  max-width: none; /* the intro runs the full width */
}
.intro b {
  color: var(--ink);
}
.subtabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}
.subtabs button {
  min-height: 0;
  padding: 8px 14px;
  border: 0;
  border-radius: 999px;
  background: var(--surface);
  box-shadow: inset 0 0 0 1.5px var(--line);
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
}
.subtabs button[aria-pressed='true'] {
  background: var(--navy);
  box-shadow: none;
  font-weight: 600;
  color: var(--on-navy);
}
.pipe {
  margin: 0 8px;
  font-weight: 400;
  opacity: 0.4;
}
</style>
