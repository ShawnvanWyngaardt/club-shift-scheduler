<script setup lang="ts">
/**
 * Circled exclamation mark, for error / failed states.
 *
 * Same API as IconCheckCircle:
 * Colour: defaults to `currentColor`; override with `color` (any CSS colour or var).
 * Size: `size` sets width and height (number = px, or any CSS length).
 * Decorative by default (aria-hidden). Pass `label` to make it announce itself.
 */
withDefaults(
  defineProps<{
    size?: number | string
    color?: string
    strokeWidth?: number
    label?: string
  }>(),
  { size: 24, color: 'currentColor', strokeWidth: 2 },
)
</script>

<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    :width="size"
    :height="size"
    fill="none"
    :stroke="color"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    :role="label ? 'img' : undefined"
    :aria-label="label"
    :aria-hidden="label ? undefined : 'true'"
    focusable="false"
    class="icon"
  >
    <circle cx="12" cy="12" r="10" />
    <path d="M12 7v6" />
    <path d="M12 16.5h.01" />
  </svg>
</template>

<style scoped>
.icon {
  flex-shrink: 0;
}
</style>
