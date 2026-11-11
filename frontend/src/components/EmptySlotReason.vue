<script setup lang="ts">
import { computed } from 'vue'
import type { BlockedMember } from '@/api'

const props = defineProps<{ blocked: BlockedMember[] }>()

const lines = computed(() =>
  props.blocked.length === 0
    ? ['Nobody said they could do this shift yet.']
    : props.blocked.map((b) =>
        b.reason === 'busy_at_that_time'
          ? `${b.member_name} said yes, but already has a shift at that time.`
          : `${b.member_name} said yes and is already on this shift.`,
      ),
)
</script>

<template>
  <ul class="reasons">
    <li v-for="line in lines" :key="line" class="muted">{{ line }}</li>
  </ul>
</template>

<style scoped>
.reasons {
  margin: var(--space-1, 4px) 0 0;
  padding-left: 1.25rem;
  font-size: 0.9375rem;
}
</style>
