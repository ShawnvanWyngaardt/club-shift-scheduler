import type { AssignmentDetail, ShiftDetail, ShiftTypeInfo } from '@/api'
import { clubDateInput, formatTime } from '@/time'

/** What each points value means, in the coordinator's words. */
export const WEIGHT_LABELS: Record<number, string> = {
  1: 'easy to fill',
  2: 'takes some asking',
  3: 'nobody wants it',
}

export interface ShiftRow {
  shift: ShiftDetail
  /** People on it. While anyone is, its time can't change (the API refuses). */
  taken: number
}

export interface TypeGroup {
  type: ShiftTypeInfo
  /** Shifts that haven't started, soonest first: the only ones that can still change. */
  upcoming: ShiftRow[]
  /** Every shift of this type, past ones included. A type can only be removed at 0. */
  total: number
}

/** Shifts grouped under their type, in the order the types were made. */
export function typeGroups(
  types: ShiftTypeInfo[],
  shifts: ShiftDetail[],
  assignments: Pick<AssignmentDetail, 'shift_id'>[],
  now: Date = new Date(),
): TypeGroup[] {
  const taken = new Map<number, number>()
  for (const a of assignments) taken.set(a.shift_id, (taken.get(a.shift_id) ?? 0) + 1)

  return types.map((type) => {
    const ofType = shifts.filter((s) => s.shift_type_id === type.id)
    const upcoming = ofType
      .filter((s) => new Date(s.starts_at).getTime() > now.getTime())
      .sort((a, b) => a.starts_at.localeCompare(b.starts_at))
      .map((shift) => ({ shift, taken: taken.get(shift.id) ?? 0 }))
    return { type, upcoming, total: ofType.length }
  })
}

export interface ShiftForm {
  date: string
  start: string
  end: string
  slots: number
}

/** An existing shift as the edit form's values, on the club clock. */
export function formFor(shift: ShiftDetail): ShiftForm {
  return {
    date: clubDateInput(shift.starts_at),
    start: formatTime(shift.starts_at),
    end: formatTime(shift.ends_at),
    slots: shift.slots,
  }
}

/** Did the date or times change? A new time clears who was available for it. */
export const timeChanged = (before: ShiftForm, after: ShiftForm) =>
  before.date !== after.date || before.start !== after.start || before.end !== after.end
