import { describe, expect, it } from 'vitest'
import type { ShiftDetail } from '@/api'
import { formFor, timeChanged, typeGroups } from '@/shifts'

const now = new Date('2026-11-24T12:00:00Z')
const types = [
  { id: 1, name: 'Bar', weight: 3 },
  { id: 2, name: 'Kit wash', weight: 1 },
  { id: 3, name: 'Gate', weight: 2 },
]
const shift = (id: number, typeId: number, starts_at: string, slots = 2): ShiftDetail => ({
  id,
  shift_type_id: typeId,
  shift_type: '',
  weight: 0,
  starts_at,
  ends_at: starts_at.replace('T08', 'T11'),
  slots,
})
const shifts = [
  shift(10, 1, '2026-12-05T08:00:00Z'),
  shift(11, 1, '2026-11-28T08:00:00Z'), // sooner: listed first
  shift(12, 1, '2026-11-21T08:00:00Z'), // past: not listed, but still counts
  shift(20, 2, '2026-11-14T08:00:00Z'), // a type with only past shifts
]

describe('typeGroups', () => {
  const groups = typeGroups(types, shifts, [{ shift_id: 11 }, { shift_id: 11 }], now)

  it('groups upcoming shifts under their type, soonest first, with who is on them', () => {
    expect(groups[0]!.upcoming.map((r) => [r.shift.id, r.taken])).toEqual([
      [11, 2],
      [10, 0],
    ])
  })

  it('counts past shifts too, because a type with any shift cannot be removed', () => {
    expect(groups.map((g) => [g.type.name, g.upcoming.length, g.total])).toEqual([
      ['Bar', 2, 3],
      ['Kit wash', 0, 1],
      ['Gate', 0, 0],
    ])
  })
})

describe('the edit form', () => {
  it('shows a shift on the club clock', () => {
    // 08:00 UTC in winter is 09:00 in Amsterdam
    expect(formFor(shift(10, 1, '2026-12-05T08:00:00Z', 3))).toEqual({
      date: '2026-12-05',
      start: '09:00',
      end: '12:00',
      slots: 3,
    })
  })

  it('tells a new time from a new number of people', () => {
    const before = { date: '2026-12-05', start: '09:00', end: '12:00', slots: 3 }
    expect(timeChanged(before, { ...before, slots: 4 })).toBe(false)
    expect(timeChanged(before, { ...before, start: '10:00' })).toBe(true)
  })
})
