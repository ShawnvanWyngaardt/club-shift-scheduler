<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { coordinatorApi, type ShiftTypeInfo } from '@/api'
import MemberList from '@/components/MemberList.vue'
import ShiftsSection from '@/components/setup/ShiftsSection.vue'
import ShiftTypesSection from '@/components/setup/ShiftTypesSection.vue'

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

const memberCount = ref<number | null>(null)
const shiftTypes = ref<ShiftTypeInfo[]>([])

async function loadCounts() {
  const id = Number(props.clubId)
  const [links, types] = await Promise.allSettled([
    coordinatorApi.memberLinks(id, props.token),
    coordinatorApi.shiftTypes(id),
  ])
  if (links.status === 'fulfilled') memberCount.value = links.value.length
  if (types.status === 'fulfilled') shiftTypes.value = types.value
}

async function loadShiftTypes() {
  try {
    shiftTypes.value = await coordinatorApi.shiftTypes(Number(props.clubId))
  } catch {
    shiftTypes.value = []
  }
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
        Shifts<span class="pipe" aria-hidden="true">|</span>{{ shiftTypes.length }}
        {{ shiftTypes.length === 1 ? 'type' : 'types' }}
      </button>
    </div>

    <MemberList
      v-if="section === 'members'"
      :club-id="clubId"
      :token="token"
      @count="memberCount = $event"
    />

    <!-- Restyled in the next slice -->
    <template v-else>
      <ShiftTypesSection
        :club-id="clubId"
        :token="token"
        :shift-types="shiftTypes"
        @changed="loadShiftTypes"
      />
      <ShiftsSection :club-id="clubId" :token="token" :shift-types="shiftTypes" />
    </template>
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
