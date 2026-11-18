import { computed, nextTick, onBeforeUnmount, ref, watch, type Ref } from 'vue'
import { useRoute } from 'vue-router'

/*
 * The sliding tab indicator, shared by the member and coordinator layouts.
 * One bar for the whole nav, moved under the active tab. The layout stays mounted
 * when the tab changes (only the RouterView swaps), so the bar survives and CSS
 * can animate it from the old tab to the new one.
 */
export function useSlidingTabBar(
  nav: Ref<HTMLElement | null>,
  activeSelector = '.router-link-exact-active',
) {
  const route = useRoute()
  const bar = ref({ x: 0, y: 0, width: 0 })
  const animate = ref(false) // off for the first placement, so it doesn't slide in from the left

  function moveBar() {
    const active = nav.value?.querySelector<HTMLElement>(activeSelector)
    if (!nav.value || !active) return
    const box = nav.value.getBoundingClientRect()
    const tab = active.getBoundingClientRect()
    bar.value = { x: tab.left - box.left, y: tab.bottom - box.top - 4, width: tab.width }
  }

  // Re-measure when the tab changes, and when the nav appears after loading.
  watch([() => route.name, nav], async () => {
    await nextTick() // wait for the new active class (and its bolder, wider text)
    moveBar()
    requestAnimationFrame(() => (animate.value = true))
  })

  // Re-measure when the nav changes size: window resize, tabs wrapping, fonts loading.
  const resize = new ResizeObserver(moveBar)
  watch(nav, (el, old) => {
    if (old) resize.unobserve(old)
    if (el) resize.observe(el)
  })
  onBeforeUnmount(() => resize.disconnect())

  const barStyle = computed(() => ({
    width: `${bar.value.width}px`,
    transform: `translate(${bar.value.x}px, ${bar.value.y}px)`,
  }))

  return { barStyle, animate }
}
