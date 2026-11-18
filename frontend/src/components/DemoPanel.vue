<script setup lang="ts">
import { points } from "@/format";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import type { DemoClub } from "@/api";
import { memberUrl } from "@/links";

const props = defineProps<{ demo: DemoClub }>();

const visitor = computed(() => props.demo.members[0]);
const others = computed(() => props.demo.members.slice(1));
const copied = ref<string | null>(null);

async function copyLink(token: string) {
  try {
    await navigator.clipboard.writeText(memberUrl(token));
    copied.value = token;
  } catch {
    copied.value = null;
  }
}

/*
 * The two disclosures open like a menu: a panel floating over the page below the
 * card, so nothing underneath moves. One open at a time; a click outside or
 * Escape closes it.
 */
const card = ref<HTMLElement | null>(null);

function openMenus() {
  return [...(card.value?.querySelectorAll<HTMLDetailsElement>("details[open]") ?? [])];
}

function onToggle(event: Event) {
  const opened = event.target as HTMLDetailsElement;
  if (!opened.open) return;
  for (const other of openMenus()) if (other !== opened) other.open = false;
}

function onPointerDown(event: PointerEvent) {
  if (card.value && !card.value.contains(event.target as Node)) {
    for (const menu of openMenus()) menu.open = false;
  }
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== "Escape") return;
  for (const menu of openMenus()) {
    const hadFocus = menu.contains(document.activeElement);
    menu.open = false;
    if (hadFocus) menu.querySelector("summary")?.focus(); // don't leave keyboard focus nowhere
  }
}

onMounted(() => {
  document.addEventListener("pointerdown", onPointerDown);
  document.addEventListener("keydown", onKeydown);
});
onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", onPointerDown);
  document.removeEventListener("keydown", onKeydown);
});
</script>

<template>
  <!-- Compact, so it can sit in the coordinator header on every page of a demo. -->
  <section v-if="visitor" ref="card" class="demo" aria-labelledby="demo-title">
    <h2 id="demo-title">Your private demo club</h2>
    <p class="note">Sample data, deleted after 24 hours.</p>
    <div class="btn-row">
      <a
        class="btn btn-small btn-secondary"
        :href="memberUrl(visitor.token)"
        target="_blank"
        rel="noopener"
      >
        Open as {{ visitor.name }} <em>(member)</em
        ><span class="sr-only"> (opens in a new tab)</span>
      </a>
      <button
        type="button"
        class="btn btn-small btn-ghost"
        @click="copyLink(visitor.token)"
      >
        {{ copied === visitor.token ? "Copied" : "Copy link for your phone" }}
      </button>
    </div>

    <details @toggle="onToggle">
      <summary>How to try it, in 3 steps</summary>
      <ol class="menu">
        <li>
          Open the member page as {{ visitor.name }}, tick the shifts you'd do, and save.
        </li>
        <li>Come back to this tab and generate a schedule.</li>
        <li>
          Publish it, then open the member's <strong>My shifts</strong> tab to see what
          you were given and why.
        </li>
      </ol>
    </details>

    <details @toggle="onToggle">
      <summary>Other members' links ({{ others.length }})</summary>
      <ul class="menu members">
        <li v-for="member in others" :key="member.token">
          <a :href="memberUrl(member.token)" target="_blank" rel="noopener">{{
            member.name
          }}</a>
          <span class="note">{{ points(member.points, { short: true }) }}</span>
          <button
            type="button"
            class="btn btn-small btn-edit"
            @click="copyLink(member.token)"
          >
            {{ copied === member.token ? "Copied" : "Copy link" }}
          </button>
        </li>
      </ul>
    </details>
  </section>
</template>

<style scoped>
/* Same card language as the shift cards: white, soft shadow, a coloured right edge. */
.demo {
  position: relative; /* the menus are placed under the card */
  width: min(100%, 400px);
  padding: 12px 16px;
  background: var(--surface);
  border-radius: var(--r);
  border-right: 3px solid var(--sky);
  box-shadow: var(--shadow);
}
h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--heading);
}
.note {
  margin: 2px 0 10px;
  font-size: 13px;
  color: var(--muted);
}
details {
  margin-top: 8px;
  font-size: 13px;
}
summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--navy);
}
/* An open menu floats over the page instead of pushing it down */
.menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 10; /* above the sticky notice bar */
  max-height: min(60vh, 420px); /* a long members list scrolls inside the menu */
  overflow-y: auto;
  margin: 0;
  padding: 12px 16px;
  background: var(--surface);
  border-radius: var(--r);
  box-shadow: 0 8px 24px -8px rgba(20, 30, 40, 0.3);
}
ol.menu {
  padding-left: 36px;
}
li {
  margin-bottom: 4px;
}
.members {
  list-style: none;
}
.members li {
  display: flex;
  align-items: center;
  gap: 8px;
}
.members .note {
  margin: 0;
  flex: 1;
}
a:not(.btn) {
  color: var(--navy);
  font-weight: 600;
}
</style>
