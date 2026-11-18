import { describe, expect, it } from 'vitest'
import { findMembers, historyFor, memberRows, pageOf, parseReason } from '@/members'

const links = [
  { id: 1, name: 'Daan', access_token: 'd-code' },
  { id: 2, name: 'anna', access_token: 'a-code' },
  { id: 3, name: 'Bram', access_token: 'b-code' },
  { id: 4, name: 'Cas', access_token: 'c-code' },
  { id: 5, name: 'Eva', access_token: 'e-code' },
]
const balances = [
  { member_id: 1, name: 'Daan', balance: 6 },
  { member_id: 2, name: 'anna', balance: 0 },
  { member_id: 3, name: 'Bram', balance: -3 },
  { member_id: 4, name: 'Cas', balance: 3 },
  { member_id: 5, name: 'Eva', balance: 0 }, // the ledger lists every member, even at 0
]

describe('member rows', () => {
  const rows = memberRows(links, balances)

  it('joins links and points, and marks the first four in line', () => {
    expect(rows.map((r) => [r.name, r.points, r.next])).toEqual([
      ['Daan', 6, false], // most points: the only one not in the first four
      ['anna', 0, true],
      ['Bram', -3, true],
      ['Cas', 3, true],
      ['Eva', 0, true],
    ])
  })

  it('counts a member missing from the balances as 0 points', () => {
    expect(memberRows(links, balances.slice(0, 4))[4]!.points).toBe(0)
  })

  it('searches without minding capitals, and sorts by name or points', () => {
    expect(findMembers(rows, 'AN', 'name').map((r) => r.name)).toEqual(['anna', 'Daan'])
    expect(findMembers(rows, '', 'points').map((r) => r.name)).toEqual([
      'Bram',
      'anna',
      'Eva',
      'Cas',
      'Daan',
    ])
  })
})

describe('pageOf', () => {
  const list = Array.from({ length: 23 }, (_, i) => i)

  it('cuts a list into pages of ten', () => {
    expect(pageOf(list, 2)).toEqual({ items: [20, 21, 22], page: 2, pages: 3, from: 21, to: 23 })
  })

  it('falls back to the last page when a search makes the list shorter', () => {
    expect(pageOf(list.slice(0, 5), 2).page).toBe(0)
    expect(pageOf([], 0)).toEqual({ items: [], page: 0, pages: 1, from: 0, to: 0 })
  })
})

describe('history', () => {
  it('reads the reasons the backend writes', () => {
    expect(parseReason('done: Bar, Sat 21 Nov')).toEqual({
      outcome: 'Done',
      shift: 'Bar',
      date: 'Sat 21 Nov',
    })
    expect(parseReason('no_show: Kit wash, Sun 01 Nov')).toEqual({
      outcome: 'Missed',
      shift: 'Kit wash',
      date: 'Sun 01 Nov',
    })
  })

  it('copes with demo reasons that have no date, and with commas in a shift name', () => {
    expect(parseReason('done: earlier shifts this season')).toEqual({
      outcome: 'Done',
      shift: 'Earlier shifts this season',
      date: '',
    })
    expect(parseReason('done: Bar, upstairs, Sat 21 Nov').shift).toBe('Bar, upstairs')
  })

  it("keeps one member's lines, in the ledger's order", () => {
    const entries = [
      { member_id: 2, change: -3, reason: 'no_show: Bar, Sat 21 Nov', created_at: '' },
      { member_id: 1, change: 3, reason: 'done: Bar, Sat 21 Nov', created_at: '' },
      { member_id: 2, change: 2, reason: 'done: Gate, Sat 14 Nov', created_at: '' },
    ]
    expect(historyFor(entries, 2).map((h) => h.change)).toEqual([-3, 2])
  })
})
