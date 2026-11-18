import type { AssignmentDetail } from '@/api'

/** People waiting to be checked in: their shift has started and has no outcome yet. */
export function waitingForCheckIn(
  assignments: Pick<AssignmentDetail, 'status' | 'starts_at'>[],
  now: Date = new Date(),
): number {
  return assignments.filter(
    (a) => a.status === 'assigned' && new Date(a.starts_at).getTime() <= now.getTime(),
  ).length
}
