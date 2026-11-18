import { describe, expect, it } from 'vitest'
import { firstInLine, needsYou, summariseWeeks, weekStatus } from '@/overview'
import { weeksFrom } from '@/time'

// Monday 23 to Sunday 29 November is week 48, then week 49 and 50.
const weeks = weeksFrom('2026-11-24T12:00:00Z', 3)
const now = new Date('2026-11-24T12:00:00Z')

const shifts = [
  { id: 1, starts_at: '2026-11-21T08:00:00Z', slots: 2 }, // week 47: not shown
  { id: 2, starts_at: '2026-11-23T08:00:00Z', slots: 2 }, // week 48, started
  { id: 3, starts_at: '2026-11-28T08:00:00Z', slots: 2 }, // week 48
  { id: 4, starts_at: '2026-12-05T08:00:00Z', slots: 3 }, // week 49, nobody yet
]
const assignments = [
  { shift_id: 2, status: 'assigned' as const, starts_at: '2026-11-23T08:00:00Z' },
  { shift_id: 2, status: 'done' as const, starts_at: '2026-11-23T08:00:00Z' },
  { shift_id: 3, status: 'assigned' as const, starts_at: '2026-11-28T08:00:00Z' },
]

describe('summariseWeeks', () => {
  const [w48, w49, w50] = summariseWeeks(weeks, shifts, assignments)

  it('counts shifts, slots and who fills them, per week', () => {
    expect([w48!.shifts, w48!.slots, w48!.filled, w48!.empty, w48!.published]).toEqual([
      2, 4, 3, 1, true,
    ])
    expect(weekStatus(w48!)).toBe('gaps')
  })

  it('calls a week with shifts but no assignments not published', () => {
    expect(weekStatus(w49!)).toBe('unpublished')
  })

  it('keeps an empty week, so the Overview still shows four rows', () => {
    expect(weekStatus(w50!)).toBe('no-shifts')
  })
})

describe('available members per week', () => {
  it('counts each member once per week', () => {
    const pairs = [
      { shift_id: 2, member_id: 7 },
      { shift_id: 3, member_id: 7 }, // same week, same member
      { shift_id: 3, member_id: 8 },
      { shift_id: 4, member_id: 7 }, // week 49
      { shift_id: 1, member_id: 9 }, // week 47: not shown
    ]
    const summaries = summariseWeeks(weeks, shifts, assignments, pairs)
    expect(summaries.map((s) => s.available)).toEqual([2, 1, 0])
  })
})

describe('needsYou', () => {
  const summaries = summariseWeeks(weeks, shifts, assignments)
  const needs = needsYou(summaries, assignments, now)

  it('puts check-ins first, then gaps, then weeks to publish', () => {
    expect(needs.map((n) => n.action)).toEqual(['Check in', 'Fill the gap', 'Fill slots'])
  })

  it('says how many people and from which day', () => {
    expect(needs[0]!.title).toBe('1 person to check in, from Monday 23 November')
  })

  it('links each week to its week page', () => {
    expect(needs[1]!.to).toEqual({ name: 'week', week: '2026-W48' })
    expect(needs[2]!.title).toBe("Week 49 isn't published yet")
  })

  it('is empty when there is nothing to do', () => {
    expect(needsYou([], [], now)).toEqual([])
  })
})

describe('firstInLine', () => {
  it('takes the fewest points first, then the name', () => {
    const balances = [
      { member_id: 1, name: 'Daan', balance: 3 },
      { member_id: 2, name: 'Bram', balance: 0 },
      { member_id: 3, name: 'Anna', balance: 0 },
      { member_id: 4, name: 'Cas', balance: -3 },
    ]
    expect(firstInLine(balances, 3).map((b) => b.name)).toEqual(['Cas', 'Anna', 'Bram'])
  })
})
