import type { Ledger, LedgerEntry, MemberLink } from '@/api'
import { firstInLine } from '@/overview'

export const PAGE_SIZE = 10

export interface MemberRow {
  id: number
  name: string
  /** Their personal code: the last part of their link */
  token: string
  points: number
  /** Among the first in line for the next shifts */
  next: boolean
}

export type MemberSort = 'name' | 'points'

/** Links and balances, joined into one row per member. */
export function memberRows(links: MemberLink[], balances: Ledger['balances']): MemberRow[] {
  const points = new Map(balances.map((b) => [b.member_id, b.balance]))
  const next = new Set(firstInLine(balances).map((b) => b.member_id))
  return links.map((link) => ({
    id: link.id,
    name: link.name,
    token: link.access_token,
    points: points.get(link.id) ?? 0,
    next: next.has(link.id),
  }))
}

/** Search by name, then sort: by name, or fewest points first like the schedule does. */
export function findMembers(rows: MemberRow[], query: string, sort: MemberSort): MemberRow[] {
  const q = query.trim().toLocaleLowerCase()
  return rows
    .filter((r) => !q || r.name.toLocaleLowerCase().includes(q))
    .sort((a, b) =>
      sort === 'points'
        ? a.points - b.points || a.name.localeCompare(b.name)
        : a.name.localeCompare(b.name),
    )
}

/** One page of a list. A page past the end falls back to the last page. */
export function pageOf<T>(list: T[], page: number, size = PAGE_SIZE) {
  const pages = Math.max(1, Math.ceil(list.length / size))
  const current = Math.min(Math.max(0, page), pages - 1)
  const start = current * size
  const items = list.slice(start, start + size)
  return { items, page: current, pages, from: list.length ? start + 1 : 0, to: start + items.length }
}

export interface HistoryLine {
  change: number
  shift: string
  /** "Sat 21 Nov", or empty for entries without a date */
  date: string
  outcome: 'Done' | 'Missed' | ''
}

/*
 * The backend writes each reason as "done: Bar, Sat 21 Nov" (routers/outcomes.py).
 * Demo data has reasons without a date, like "done: earlier shifts this season".
 */
export function parseReason(reason: string): Omit<HistoryLine, 'change'> {
  const match = /^(done|no_show):\s*(.*)$/.exec(reason)
  const outcome = match?.[1] === 'done' ? 'Done' : match?.[1] === 'no_show' ? 'Missed' : ''
  const rest = match?.[2] ?? reason
  const split = rest.lastIndexOf(', ')
  const dated = split >= 0 && /^\w{3} \d{1,2} \w{3}$/.test(rest.slice(split + 2))
  const shift = dated ? rest.slice(0, split) : rest
  return {
    outcome,
    shift: shift.charAt(0).toUpperCase() + shift.slice(1),
    date: dated ? rest.slice(split + 2) : '',
  }
}

/** One member's points history, newest first, as the ledger already orders it. */
export function historyFor(entries: LedgerEntry[], memberId: number): HistoryLine[] {
  return entries
    .filter((e) => e.member_id === memberId)
    .map((e) => ({ change: e.change, ...parseReason(e.reason) }))
}
