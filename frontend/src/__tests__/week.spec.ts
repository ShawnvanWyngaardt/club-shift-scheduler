import { describe, expect, it } from 'vitest'
import type { AssignmentDetail, Proposal, ShiftDetail } from '@/api'
import { openSlots, shiftCards } from '@/week'

const now = new Date('2026-11-24T12:00:00Z')

const shift = (id: number, starts_at: string, slots: number): ShiftDetail => ({
  id,
  shift_type_id: 1,
  shift_type: 'Bar',
  weight: 3,
  starts_at,
  ends_at: starts_at,
  slots,
})
const on = (shift_id: number, member_name: string): AssignmentDetail => ({
  id: shift_id * 100 + member_name.length,
  shift_id,
  member_id: member_name.length,
  member_name,
  status: 'assigned',
  shift_type: 'Bar',
  starts_at: '',
  ends_at: '',
  weight: 3,
})

const shifts = [
  shift(1, '2026-11-28T08:00:00Z', 3), // Daan on it; Anna could join; one more nobody
  shift(2, '2026-11-28T08:00:00Z', 1), // Bram available but busy then
  shift(3, '2026-11-23T08:00:00Z', 1), // already started
]
const assignments = [on(1, 'Daan')]
const proposal: Proposal = {
  assignments: [{ shift_id: 1, member_id: 9, member_name: 'Anna' }],
  unfilled: [
    { shift_id: 1, missing: 1, blocked: [] },
    {
      shift_id: 2,
      missing: 1,
      blocked: [{ member_id: 4, member_name: 'Bram', reason: 'busy_at_that_time' }],
    },
    { shift_id: 3, missing: 1, blocked: [] },
  ],
}

describe('shiftCards', () => {
  it('explains each empty slot before the preview is shown', () => {
    const [first, second, third] = shiftCards(shifts, assignments, proposal, false, now)
    expect(first!.emptySlots.map((r) => r.title)).toEqual([
      'Anna is available',
      'Nobody else is available',
    ])
    expect(second!.emptySlots).toEqual([
      { title: 'Bram is available', text: 'but already has a shift at that time.' },
    ])
    expect([third!.started, third!.emptySlots[0]!.title]).toEqual([true, 'Nobody is available'])
  })

  it('shows who the preview adds, and only the slots that stay empty', () => {
    const [first] = shiftCards(shifts, assignments, proposal, true, now)
    expect(first!.added).toEqual(['Anna'])
    expect(first!.emptySlots.map((r) => r.title)).toEqual(['Nobody else is available'])
  })

  it('works without a proposal, for a full or past week', () => {
    const [first] = shiftCards(shifts, assignments, null, false, now)
    expect(first!.emptySlots.length).toBe(2)
  })

  it('counts only empty slots that can still be filled', () => {
    expect(openSlots(shiftCards(shifts, assignments, proposal, false, now))).toBe(3)
  })
})
