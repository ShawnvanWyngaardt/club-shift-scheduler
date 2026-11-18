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

export type Mark = 'done' | 'no_show'

/** One shift on the Check-in page, with everyone who was on it. */
export interface CheckInGroup {
  shiftId: number
  shiftType: string
  startsAt: string
  endsAt: string
  weight: number
  people: AssignmentDetail[]
}

/**
 * Shifts that still have someone to check in, oldest first. Split into shifts that
 * have started (the real work) and upcoming ones: the API accepts those too, which
 * lets a demo visitor try the page before any shift has happened.
 */
export function checkInGroups(assignments: AssignmentDetail[], now: Date = new Date()) {
  const byShift = new Map<number, CheckInGroup>()
  for (const a of assignments) {
    const group = byShift.get(a.shift_id) ?? {
      shiftId: a.shift_id,
      shiftType: a.shift_type,
      startsAt: a.starts_at,
      endsAt: a.ends_at,
      weight: a.weight,
      people: [],
    }
    group.people.push(a)
    byShift.set(a.shift_id, group)
  }
  const open = [...byShift.values()]
    .filter((g) => g.people.some((p) => p.status === 'assigned'))
    .sort((a, b) => a.startsAt.localeCompare(b.startsAt))
  const started = (g: CheckInGroup) => new Date(g.startsAt).getTime() <= now.getTime()
  return { started: open.filter(started), upcoming: open.filter((g) => !started(g)) }
}

/** The notice after saving: "2 checks saved for Bar." / "1 did the shift, 1 missed it." */
export function savedNotice(shiftType: string, marks: Mark[]) {
  const did = marks.filter((m) => m === 'done').length
  const missed = marks.length - did
  return {
    title: `${marks.length} ${marks.length === 1 ? 'check' : 'checks'} saved for ${shiftType}.`,
    detail: `${did} did the shift, ${missed} missed it. Their points are updated.`,
  }
}
