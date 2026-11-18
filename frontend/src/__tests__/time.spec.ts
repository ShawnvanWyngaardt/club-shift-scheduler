import { describe, expect, it } from 'vitest'
import {
  amsterdamToIso,
  formatDay,
  formatShortDay,
  formatTime,
  formatTimeRange,
  groupByWeek,
  weekFromKey,
  weekOf,
  weeksFrom,
} from '@/time'

describe('time formatting', () => {
  it('turns club time into the right UTC moment on both sides of the clock change', () => {
    expect(amsterdamToIso('2026-10-24', '07:00')).toBe('2026-10-24T05:00:00.000Z')
    expect(amsterdamToIso('2026-10-31', '07:00')).toBe('2026-10-31T06:00:00.000Z')
  })

  it('shows UTC times from the API in Amsterdam time', () => {
    expect(formatTimeRange('2026-10-24T05:00:00Z', '2026-10-24T09:00:00Z')).toBe('07:00 – 11:00')
  })

  it('uses Amsterdam winter time after the clocks change', () => {
    expect(formatTimeRange('2026-10-31T06:00:00Z', '2026-10-31T10:00:00Z')).toBe('07:00 – 11:00')
  })

  it('has short forms for narrow column headers', () => {
    expect([formatShortDay('2026-11-28T06:00:00Z'), formatTime('2026-11-28T06:00:00Z')]).toEqual([
      'Sat 28',
      '07:00',
    ])
  })

  it('puts a late-evening UTC time on the right Amsterdam day', () => {
    expect(formatDay('2026-10-23T23:30:00Z')).toBe('Saturday 24 October')
  })
})

describe('club weeks', () => {
  it('finds the Monday-to-Sunday week on the club clock', () => {
    expect(weekOf('2026-11-16T10:00:00Z')).toEqual({
      key: '2026-W47',
      number: 47,
      dates: '16 – 22 Nov',
      start: '2026-11-15T23:00:00.000Z', // Monday 00:00 in Amsterdam
      end: '2026-11-22T23:00:00.000Z', // the next Monday 00:00
    })
    // 23:30 on Sunday in Amsterdam is still the same week, though it's Sunday 22:30 in UTC.
    expect(weekOf('2026-11-22T22:30:00Z').key).toBe('2026-W47')
  })

  it('names both months when a week crosses into the next one', () => {
    expect(weekOf('2026-12-05T07:00:00Z').dates).toBe('30 Nov – 6 Dec')
  })

  it('gives the first days of January to the last week of the old year when ISO says so', () => {
    expect(weekOf('2027-01-03T12:00:00Z').key).toBe('2026-W53')
    expect(weekOf('2027-01-04T12:00:00Z').key).toBe('2027-W01')
  })

  it('keeps the range right across the clock change', () => {
    // Clocks go back on Sunday 25 October: Monday 19 starts in summer time, Monday 26 in winter time.
    const week = weekOf('2026-10-21T12:00:00Z')
    expect([week.start, week.end]).toEqual(['2026-10-18T22:00:00.000Z', '2026-10-25T23:00:00.000Z'])
  })

  it('reads a week back from its URL key, and refuses weeks that do not exist', () => {
    expect(weekFromKey('2026-W47')).toEqual(weekOf('2026-11-16T10:00:00Z'))
    expect(weekFromKey('2026-W53')?.dates).toBe('28 Dec – 3 Jan')
    expect(weekFromKey('2027-W53')).toBeNull()
    expect(weekFromKey('week-47')).toBeNull()
  })

  it('lists this week and the next ones, over a year end', () => {
    expect(weeksFrom('2026-12-24T09:00:00Z', 3).map((w) => w.key)).toEqual([
      '2026-W52',
      '2026-W53',
      '2027-W01',
    ])
  })

  it('groups items by week in the order they come in', () => {
    const groups = groupByWeek([
      { starts_at: '2026-11-21T06:00:00Z' },
      { starts_at: '2026-11-22T07:00:00Z' },
      { starts_at: '2026-11-28T06:00:00Z' },
    ])
    expect(groups.map((g) => [g.week.number, g.items.length])).toEqual([
      [47, 2],
      [48, 1],
    ])
  })
})
