import { onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ApiError, demoApi } from '@/api'
import { rememberDemo } from '@/demo'

/**
 * Starting a demo from anywhere on the landing page: the hero and the closing
 * call to action share this, so the waiting state and errors behave the same.
 */
export function useStartDemo() {
  const router = useRouter()
  const phase = ref<'idle' | 'starting' | 'waking' | 'full' | 'failed'>('idle')
  let slowTimer: number | undefined

  const isBusy = () => phase.value === 'starting' || phase.value === 'waking'

  async function startDemo() {
    if (isBusy()) return
    phase.value = 'starting'
    // After a quiet spell the server and database need to wake up first.
    slowTimer = window.setTimeout(() => {
      if (phase.value === 'starting') phase.value = 'waking'
    }, 4000)
    try {
      const demo = await demoApi.start()
      rememberDemo(demo)
      await router.push({
        name: 'schedule',
        params: { clubId: String(demo.club_id), token: demo.coordinator_token },
      })
    } catch (error) {
      phase.value = error instanceof ApiError && error.status === 503 ? 'full' : 'failed'
    } finally {
      window.clearTimeout(slowTimer)
    }
  }

  onBeforeUnmount(() => window.clearTimeout(slowTimer))

  return { phase, isBusy, startDemo }
}
