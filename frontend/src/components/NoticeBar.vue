<script setup lang="ts">
import { useNotice } from '@/composables/useNotice'

const { notice, closeNotice } = useNotice()
</script>

<template>
  <!-- The status region is always there, so screen readers announce what appears in it. -->
  <div class="notice" :class="{ open: notice }" role="status">
    <div v-if="notice" class="wrap notice-inner">
      <span class="notice-icon" aria-hidden="true">✓</span>
      <p class="notice-text">
        {{ notice.title }}
        <span v-if="notice.detail">{{ notice.detail }}</span>
      </p>
      <button type="button" class="notice-close" aria-label="Close message" @click="closeNotice">
        ×
      </button>
    </div>
  </div>
</template>

<style scoped>
.notice {
  position: sticky;
  top: env(safe-area-inset-top, 0px);
  z-index: 5;
}
/* Full-width band; the content inside lines up with the page */
.notice.open {
  background: var(--mint-surface);
  border-bottom: 1px solid color-mix(in srgb, var(--green) 45%, transparent);
}
.notice-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-block: 12px;
}
.notice-icon {
  flex: none;
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--green);
  color: #053b2a;
  font-size: 13px;
  font-weight: 800;
}
.notice-text {
  flex: 1;
  min-width: 0;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
.notice-text span {
  font-weight: 400;
  color: var(--muted);
}
.notice-close {
  flex: none;
  width: 36px;
  min-height: 36px;
  padding: 0;
  border-radius: 10px;
  background: none;
  color: var(--ink);
  font-size: 20px;
  line-height: 1;
}
.notice-close:hover {
  background: color-mix(in srgb, var(--ink) 8%, transparent);
}
@media (prefers-reduced-motion: no-preference) {
  .notice-inner {
    animation: drop 220ms ease-out;
  }
}
@keyframes drop {
  from {
    transform: translateY(-8px);
    opacity: 0;
  }
}
</style>
