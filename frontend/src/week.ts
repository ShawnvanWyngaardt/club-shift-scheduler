import type { AssignmentDetail, AvailabilityPair, Ledger, Proposal, ShiftDetail } from '@/api'

/*
 * What one shift card on the Week page shows: who is on it, who a preview
 * would add, and a reason for every empty slot.
 *
 * The reasons come from the solver. The Week page asks it for a proposal as soon
 * as it loads (that saves nothing), so an empty slot can say "Anna is available"
 * or "Nobody is available" before anyone clicks a button.
 */

export interface SlotReason {
  title: string
  text: string
}

export interface ShiftCard {
  shift: ShiftDetail
  holders: AssignmentDetail[]
  /** Names the preview would add. Only filled while the preview is showing. */
  added: string[]
  /** One reason per empty slot, in slot order. */
  emptySlots: SlotReason[]
  /** The API refuses changes once a shift has started, so the page hides the buttons. */
  started: boolean
}

const names = (list: string[]) =>
  list.length <= 2
    ? list.join(' and ')
    : `${list.slice(0, -1).join(', ')} and ${list[list.length - 1]}`
const isAre = (list: string[]) => (list.length === 1 ? 'is' : 'are')

const nobody = (holders: number): SlotReason => ({
  title: holders > 0 ? 'Nobody else is available' : 'Nobody is available',
  text: 'Assign someone by hand, or ask the group.',
})

export function shiftCards(
  shifts: ShiftDetail[],
  assignments: AssignmentDetail[],
  proposal: Proposal | null,
  showPreview: boolean,
  now: Date = new Date(),
): ShiftCard[] {
  const holdersOf = new Map<number, AssignmentDetail[]>()
  for (const a of assignments) holdersOf.set(a.shift_id, [...(holdersOf.get(a.shift_id) ?? []), a])

  const proposedFor = new Map<number, string[]>()
  for (const a of proposal?.assignments ?? []) {
    proposedFor.set(a.shift_id, [...(proposedFor.get(a.shift_id) ?? []), a.member_name])
  }
  const unfilled = new Map((proposal?.unfilled ?? []).map((u) => [u.shift_id, u]))

  return shifts.map((shift) => {
    const holders = holdersOf.get(shift.id) ?? []
    const proposed = proposedFor.get(shift.id) ?? []
    const added = showPreview ? proposed : []
    const empty = Math.max(0, shift.slots - holders.length - added.length)

    // Without the preview showing, the people it would add explain the first empty slots.
    const ready = showPreview ? [] : proposed
    const busy = (unfilled.get(shift.id)?.blocked ?? [])
      .filter((b) => b.reason === 'busy_at_that_time')
      .map((b) => b.member_name)

    const emptySlots = Array.from({ length: empty }, (_, i): SlotReason => {
      const name = ready[i]
      if (name) return { title: `${name} is available`, text: 'Preview the schedule to add them.' }
      if (busy.length) {
        return {
          title: `${names(busy)} ${isAre(busy)} available`,
          text: `but already ${busy.length === 1 ? 'has' : 'have'} a shift at that time.`,
        }
      }
      return nobody(holders.length + added.length + ready.length)
    })

    return { shift, holders, added, emptySlots, started: new Date(shift.starts_at) <= now }
  })
}

/** Empty slots on shifts that can still be filled: what Generate and Publish can act on. */
export const openSlots = (cards: ShiftCard[]) =>
  cards.filter((c) => !c.started).reduce((sum, c) => sum + c.emptySlots.length, 0)

/*
 * The "Who is available" grid: members down the side, this week's shifts across.
 * Each cell says whether the member is on the shift, would be added by the preview,
 * is available, or isn't.
 */
export type Cell = 'on' | 'new' | 'yes' | 'no'

export interface GridColumn {
  shift: ShiftDetail
  filled: number
  /** Still has an empty slot, counting the preview */
  gap: boolean
}

export interface GridRow {
  memberId: number
  name: string
  points: number
  cells: Cell[]
}

export function availabilityGrid(
  shifts: ShiftDetail[],
  assignments: AssignmentDetail[],
  pairs: AvailabilityPair[],
  balances: Ledger['balances'],
  added: { shift_id: number; member_id: number }[] = [],
): { columns: GridColumn[]; rows: GridRow[] } {
  const key = (shiftId: number, memberId: number) => `${shiftId}:${memberId}`
  const on = new Set(assignments.map((a) => key(a.shift_id, a.member_id)))
  const isNew = new Set(added.map((a) => key(a.shift_id, a.member_id)))
  const yes = new Set(pairs.map((p) => key(p.shift_id, p.member_id)))

  const columns = shifts.map((shift) => {
    const filled =
      assignments.filter((a) => a.shift_id === shift.id).length +
      added.filter((a) => a.shift_id === shift.id).length
    return { shift, filled, gap: filled < shift.slots }
  })

  const rows = [...balances]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((member) => ({
      memberId: member.member_id,
      name: member.name,
      points: member.balance,
      cells: shifts.map((shift): Cell => {
        const k = key(shift.id, member.member_id)
        if (on.has(k)) return 'on'
        if (isNew.has(k)) return 'new'
        return yes.has(k) ? 'yes' : 'no'
      }),
    }))

  return { columns, rows }
}

/** How many members are available for at least one of these shifts. */
export const availableMembers = (pairs: AvailabilityPair[]) =>
  new Set(pairs.map((p) => p.member_id)).size
