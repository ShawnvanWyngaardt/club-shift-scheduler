import { readonly, ref } from 'vue'
import { coordinatorApi, type AssignmentDetail } from '@/api'
import { waitingForCheckIn } from '@/checkin'

/*
 * The orange count on the Check-in tab. Shared at module level, so the Check-in
 * page can update it the moment a shift is saved, without asking the server again.
 */
const waiting = ref(0)

/** Count from assignments the caller already has. */
export function updateWaiting(assignments: Pick<AssignmentDetail, 'status' | 'starts_at'>[]) {
  waiting.value = waitingForCheckIn(assignments)
}

/** Ask the server. The count is a hint, so a failed request just hides it. */
export async function refreshWaiting(clubId: number, token: string) {
  try {
    updateWaiting(await coordinatorApi.assignments(clubId, token))
  } catch {
    waiting.value = 0
  }
}

export function useWaitingCount() {
  return { waiting: readonly(waiting), updateWaiting, refreshWaiting }
}
