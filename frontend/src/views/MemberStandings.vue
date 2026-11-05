<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api, type Ledger, type MemberProfile } from '@/api'

const props = defineProps<{ token: string; profile?: MemberProfile }>()

const ledger = ref<Ledger | null>(null)
const state = ref<'loading' | 'ready' | 'error'>('loading')

async function load() {
  if (!props.profile) return
  state.value = 'loading'
  try {
    ledger.value = await api.ledger(props.token)
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

// Alphabetical on purpose: this shows that the load is shared, it isn't a leaderboard.
const rows = computed(() =>
  [...(ledger.value?.balances ?? [])].sort((a, b) => a.name.localeCompare(b.name)),
)
const isMe = (memberId: number) => memberId === props.profile?.member_id

onMounted(load)
</script>

<template>
  <main class="page">
    <p v-if="state === 'loading'" class="muted">Loading club points…</p>

    <section v-else-if="state === 'error'">
      <p class="error">We couldn't load the club's points.</p>
      <button type="button" @click="load">Try again</button>
    </section>

    <template v-else>
      <h2>Points in {{ profile?.club_name }}</h2>
      <p class="muted intro">
        Everyone's points this season, so you can see the work is shared. Whoever has the fewest
        points goes first for the next shift.
      </p>
      <ul class="row-list" aria-label="Points per member">
        <li
          v-for="row in rows"
          :key="row.member_id"
          :class="{ me: isMe(row.member_id) }"
          :aria-current="isMe(row.member_id) ? 'true' : undefined"
        >
          <span> {{ row.name }}<span v-if="isMe(row.member_id)" class="muted"> (you)</span> </span>
          <strong>{{ row.balance }}</strong>
        </li>
      </ul>
    </template>
  </main>
</template>

<style scoped>
h2 {
  font-size: 1.25rem;
  margin: 0 0 var(--space-2);
}
.intro {
  margin: 0 0 var(--space-4);
}
.row-list li.me {
  border-color: var(--color-accent);
  border-width: 2px;
}
</style>
