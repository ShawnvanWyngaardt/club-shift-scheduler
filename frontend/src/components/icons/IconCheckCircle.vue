<script setup lang="ts">
/**
 * Circled checkmark, for success / saved states.
 *
 * Colour: defaults to `currentColor`, so it follows the parent's text colour.
 *   Override with the `color` prop (any CSS colour or var), e.g. color="var(--color-text-accent)".
 * Size: `size` sets width and height (number = px, or any CSS length like "1.5em").
 * The icon is decorative by default (aria-hidden). Pass `label` to make it announce itself.
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
    <path d="M8 12.5l2.5 2.5L16 9.5" />
  </svg>
</template>

<style scoped>
.icon {
  flex-shrink: 0;
}
</style>
