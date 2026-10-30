<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DemoClub } from '@/api'
import { memberUrl } from '@/links'

const props = defineProps<{ demo: DemoClub }>()

const visitor = computed(() => props.demo.members[0])
const others = computed(() => props.demo.members.slice(1))
const copied = ref<string | null>(null)

async function copyLink(token: string) {
  try {
    await navigator.clipboard.writeText(memberUrl(token))
    copied.value = token
  } catch {
    copied.value = null
  }
}
</script>

<template>
  <section v-if="visitor" class="demo" aria-labelledby="demo-title">
    <h2 id="demo-title">Your private demo club</h2>
    <p>
      Everything here is sample data, deleted after 24 hours. Try the whole loop in three steps:
    </p>
    <ol>
      <li>
        <a :href="memberUrl(visitor.token)" target="_blank" rel="noopener">
          Open the member page as {{ visitor.name }}</a
        >, tick the shifts you'd do, and save.
        <button type="button" class="button-secondary small" @click="copyLink(visitor.token)">
          {{ copied === visitor.token ? 'Copied' : 'Copy link for your phone' }}
        </button>
      </li>
      <li>Come back to this tab and generate a schedule.</li>
      <li>Publish it, then refresh the member page to see what you were given.</li>
    </ol>

    <details>
      <summary>The other members' links ({{ others.length }})</summary>
      <ul class="members">
        <li v-for="member in others" :key="member.token">
          <a :href="memberUrl(member.token)" target="_blank" rel="noopener">{{ member.name }}</a>
          <span class="muted">{{ member.points }} pts</span>
          <button type="button" class="button-secondary small" @click="copyLink(member.token)">
            {{ copied === member.token ? 'Copied' : 'Copy link' }}
          </button>
        </li>
      </ul>
    </details>
  </section>
</template>

<style scoped>
.demo {
  border: 1px solid var(--color-accent);
  border-radius: var(--radius);
  padding: var(--space-4);
  margin-bottom: var(--space-6);
}
h2 {
  font-size: 1.125rem;
  margin: 0 0 var(--space-2);
}
p {
  margin: 0 0 var(--space-3);
}
ol {
  margin: 0 0 var(--space-3);
  padding-left: var(--space-6);
}
li {
  margin-bottom: var(--space-2);
}
a {
  color: var(--color-accent);
  font-weight: 600;
}
.small {
  min-height: 36px;
  margin-left: var(--space-2);
  font-size: 0.875rem;
}
summary {
  cursor: pointer;
  font-weight: 600;
  min-height: 44px;
  display: flex;
  align-items: center;
}
.members {
  list-style: none;
  padding: 0;
  margin: 0;
}
.members li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}
</style>
