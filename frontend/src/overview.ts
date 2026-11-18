import type { AssignmentDetail, Ledger, ShiftDetail } from '@/api'
import { waitingForCheckIn } from '@/checkin'
import { formatDay, weekOf, type ClubWeek } from '@/time'

type Shift = Pick<ShiftDetail, 'id' | 'starts_at' | 'slots'>
type Assignment = Pick<AssignmentDetail, 'shift_id' | 'status' | 'starts_at'>

export interface WeekSummary {
  week: ClubWeek
  shifts: number
  slots: number
  filled: number
  empty: number
  /**
   * The API has no "published" flag: publishing just creates assignments.
   * So a week counts as published once anyone in it has a shift.
   */
  published: boolean
}

export type WeekStatus = 'no-shifts' | 'unpublished' | 'gaps' | 'full'

export function weekStatus(summary: WeekSummary): WeekStatus {
  if (summary.shifts === 0) return 'no-shifts'
  if (!summary.published) return 'unpublished'
  return summary.empty > 0 ? 'gaps' : 'full'
}

/** One summary per week, in the order given, with weeks that have no shifts kept as zeros. */
export function summariseWeeks(
  weeks: ClubWeek[],
  shifts: Shift[],
  assignments: Assignment[],
): WeekSummary[] {
  // Anyone on the shift fills a slot, whatever their outcome later.
  const held = new Map<number, number>()
  for (const a of assignments) held.set(a.shift_id, (held.get(a.shift_id) ?? 0) + 1)

  const byWeek = new Map(
    weeks.map((week) => [
      week.key,
      { week, shifts: 0, slots: 0, filled: 0, empty: 0, published: false },
    ]),
  )
  for (const shift of shifts) {
    const summary = byWeek.get(weekOf(shift.starts_at).key)
    if (!summary) continue // outside the weeks shown
    const filled = Math.min(held.get(shift.id) ?? 0, shift.slots)
    summary.shifts += 1
    summary.slots += shift.slots
    summary.filled += filled
    summary.empty += shift.slots - filled
    if (filled > 0) summary.published = true
  }
  return [...byWeek.values()]
}

export interface Need {
  /** 'act': navy button, something to fix. 'go': green button, the next schedule step. */
  kind: 'act' | 'go'
  title: string
  text: string
  action: string
  to: { name: 'outcomes' } | { name: 'week'; week: string }
}

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

/** "Needs you": check-ins first, then gaps in published weeks, then weeks not yet published. */
export function needsYou(
  summaries: WeekSummary[],
  assignments: Assignment[],
  now: Date = new Date(),
): Need[] {
  const needs: Need[] = []

  const waiting = waitingForCheckIn(assignments, now)
  if (waiting > 0) {
    const earliest = assignments
      .filter((a) => a.status === 'assigned' && new Date(a.starts_at) <= now)
      .map((a) => a.starts_at)
      .sort()[0]
    needs.push({
      kind: 'act',
      title: `${plural(waiting, 'person', 'people')} to check in, from ${formatDay(earliest!)}`,
      text: 'Mark who turned up, so the points stay fair.',
      action: 'Check in',
      to: { name: 'outcomes' },
    })
  }

  for (const s of summaries) {
    if (weekStatus(s) === 'gaps') {
      needs.push({
        kind: 'act',
        title: `Week ${s.week.number}: ${plural(s.empty, 'empty slot', 'empty slots')} in a published schedule`,
        text: 'Assign someone by hand, or ask in the group chat.',
        action: 'Fill the gap',
        to: { name: 'week', week: s.week.key },
      })
    }
  }
  for (const s of summaries) {
    if (weekStatus(s) === 'unpublished') {
      needs.push({
        kind: 'go',
        title: `Week ${s.week.number} isn't published yet`,
        text: `${plural(s.shifts, 'shift', 'shifts')}, ${plural(s.slots, 'slot', 'slots')}. Members see their shifts once you publish.`,
        action: 'Fill slots',
        to: { name: 'week', week: s.week.key },
      })
    }
  }
  return needs
}

/** The members the next schedule will reach for first: fewest points, then by name. */
export function firstInLine(balances: Ledger['balances'], count = 4) {
  return [...balances]
    .sort((a, b) => a.balance - b.balance || a.name.localeCompare(b.name))
    .slice(0, count)
}
