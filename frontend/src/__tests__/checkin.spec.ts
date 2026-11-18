import { describe, expect, it } from 'vitest'
import type { AssignmentDetail } from '../api'
import { checkInGroups, savedNotice, waitingForCheckIn } from '../checkin'

const now = new Date('2026-11-21T12:00:00Z')

describe('waitingForCheckIn', () => {
  it('counts started shifts without an outcome', () => {
    const assignments: Pick<AssignmentDetail, 'status' | 'starts_at'>[] = [
      { status: 'assigned', starts_at: '2026-11-21T08:00:00Z' }, // started: waiting
      { status: 'assigned', starts_at: '2026-11-21T12:00:00Z' }, // starting now: waiting
      { status: 'assigned', starts_at: '2026-11-22T08:00:00Z' }, // tomorrow: not yet
      { status: 'done', starts_at: '2026-11-21T08:00:00Z' }, // already checked in
      { status: 'no_show', starts_at: '2026-11-20T08:00:00Z' },
    ]
    expect(waitingForCheckIn(assignments, now)).toBe(2)
  })

  it('is zero with nothing published', () => {
    expect(waitingForCheckIn([], now)).toBe(0)
  })
})

const person = (
  id: number,
  shift_id: number,
  starts_at: string,
  status: AssignmentDetail['status'] = 'assigned',
): AssignmentDetail => ({
  id,
  shift_id,
  member_id: id,
  member_name: `Member ${id}`,
  status,
  shift_type: 'Bar',
  starts_at,
  ends_at: starts_at,
  weight: 3,
})

describe('checkInGroups', () => {
  const assignments = [
    person(1, 20, '2026-11-21T08:00:00Z'),
    person(2, 20, '2026-11-21T08:00:00Z', 'done'), // stays in its group, shown as saved
    person(3, 10, '2026-11-14T08:00:00Z'), // older shift: first
    person(4, 30, '2026-11-28T08:00:00Z'), // not started yet
    person(5, 40, '2026-11-07T08:00:00Z', 'no_show'), // everyone checked: not shown
  ]

  it('groups by shift, oldest first, and keeps already-checked people in their group', () => {
    const { started } = checkInGroups(assignments, now)
    expect(started.map((g) => [g.shiftId, g.people.length])).toEqual([
      [10, 1],
      [20, 2],
    ])
  })

  it('keeps upcoming shifts apart, and drops shifts where everyone is checked', () => {
    const { upcoming } = checkInGroups(assignments, now)
    expect(upcoming.map((g) => g.shiftId)).toEqual([30])
  })
})

describe('savedNotice', () => {
  it('says how many were saved and what happened', () => {
    expect(savedNotice('Bar', ['done', 'no_show'])).toEqual({
      title: '2 checks saved for Bar.',
      detail: '1 did the shift, 1 missed it. Their points are updated.',
    })
    expect(savedNotice('Bar', ['done']).title).toBe('1 check saved for Bar.')
  })
})
