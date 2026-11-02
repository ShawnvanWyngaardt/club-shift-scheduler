<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { coordinatorApi, type ShiftTypeInfo } from '@/api'
import MembersSection from '@/components/setup/MembersSection.vue'
import ShiftsSection from '@/components/setup/ShiftsSection.vue'
import ShiftTypesSection from '@/components/setup/ShiftTypesSection.vue'

const props = defineProps<{ clubId: string; token: string }>()

const shiftTypes = ref<ShiftTypeInfo[]>([])

async function loadShiftTypes() {
  try {
    shiftTypes.value = await coordinatorApi.shiftTypes(Number(props.clubId))
  } catch {
    shiftTypes.value = []
  }
}

onMounted(loadShiftTypes)
</script>

<template>
  <main class="page-wide">
    <header class="intro">
      <h1>Setup</h1>
      <p class="muted">
        Three steps to get your club going: who helps, what needs doing, and when.
      </p>
    </header>
    <MembersSection :club-id="clubId" :token="token" />
    <ShiftTypesSection
      :club-id="clubId"
      :token="token"
      :shift-types="shiftTypes"
      @changed="loadShiftTypes"
    />
    <ShiftsSection :club-id="clubId" :token="token" :shift-types="shiftTypes" />
  </main>
</template>

<style scoped>
.intro {
  margin-bottom: var(--space-6);
}
</style>
