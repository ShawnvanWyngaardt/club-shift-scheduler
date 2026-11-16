<script setup lang="ts">
import { points } from '@/format'
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

const isMe = (memberId: number) => memberId === props.profile?.member_id

// You first, so you don't have to hunt for yourself in a long list. Everyone else
// alphabetical on purpose: this shows that the load is shared, it isn't a leaderboard.
const rows = computed(() => {
  const all = ledger.value?.balances ?? []
  const me = all.filter((row) => isMe(row.member_id))
  const others = all
    .filter((row) => !isMe(row.member_id))
    .sort((a, b) => a.name.localeCompare(b.name))
  return [...me, ...others]
})

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
      <section class="mb-8">
        <h2>Points in {{ profile?.club_name }}</h2>
        <p class="descriptive mb-4">
          Everyone's points this season, so you can see the work is shared. Of the members
          who can do a shift, whoever has the fewest points goes first.
        </p>
      </section>
      <ul class="cards" aria-label="Points per member">
        <li
          v-for="row in rows"
          :key="row.member_id"
          class="card"
          :class="{ me: isMe(row.member_id) }"
          :aria-current="isMe(row.member_id) ? 'true' : undefined"
        >
          <span class="card-name">
            {{ row.name }}
            <!-- The demo visitor is already called "You", so don't say it twice -->
            <span v-if="isMe(row.member_id) && row.name !== 'You'" class="you">(you)</span>
          </span>
          <span class="card-points">{{ points(row.balance) }}</span>
        </li>
      </ul>
    </template>
  </main>
</template>

<style scoped>
/* Cards: the same look as My availability and My shifts */
.cards {
  list-style: none;
  margin: 0;
  padding: 0;
}
.card {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  min-height: 56px;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius);
  box-shadow: 0px 3px 12px -5px var(--color-shadow);
  margin-bottom: var(--space-3);
}
.card-name {
  flex: 1;
  color: var(--color-text);
  font-size: 0.9375rem;
  font-weight: 600;
}
.you {
  font-weight: 400;
  margin-left: var(--space-1);
}
.card-points {
  color: #5b6688; /* lighter than the names; #909cc2 would be too faint to read (2.6:1) */
  font-size: 0.8125rem;
  font-weight: 600;
  white-space: nowrap;
}

/* Your own card: the same as an assigned shift on My availability */
.card.me {
  background: var(--color-dark-gradient);
  border-right: 3px solid var(--color-member-dark-1);
  margin-bottom: var(--space-6); /* a little space between you and everyone else */
}
.card.me .card-name,
.card.me .card-points {
  color: var(--color-bg);
}
</style>
