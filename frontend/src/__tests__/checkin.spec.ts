import { describe, expect, it } from 'vitest'
import type { AssignmentDetail } from '../api'
import { waitingForCheckIn } from '../checkin'

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
