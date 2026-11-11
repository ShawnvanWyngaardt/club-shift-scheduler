export interface MemberProfile {
  member_id: number
  name: string
  club_id: number
  club_name: string
  balance: number
}

export interface MyAssignment {
  id: number
  shift_type: string
  weight: number
  starts_at: string
  ends_at: string
  status: AssignmentStatus
}

export interface MyShift {
  id: number
  shift_type: string
  weight: number
  starts_at: string
  ends_at: string
  available: boolean
  assigned: boolean
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = Array.isArray(body.detail) ? body.detail[0]?.msg : body.detail
    throw new ApiError(response.status, typeof detail === 'string' ? detail : response.statusText)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

const member = (token: string) => `/me/${encodeURIComponent(token)}`

export const api = {
  me: (token: string) => request<MemberProfile>(member(token)),
  myShifts: (token: string) => request<MyShift[]>(`${member(token)}/shifts`),
  myAssignments: (token: string) => request<MyAssignment[]>(`${member(token)}/assignments`),
  ledger: (token: string) => request<Ledger>(`${member(token)}/ledger`),
  saveAvailability: (token: string, shiftIds: number[]) =>
    request<MyShift[]>(`${member(token)}/availability`, {
      method: 'PUT',
      body: JSON.stringify({ shift_ids: shiftIds }),
    }),
}

export interface ClubPublic {
  id: number
  name: string
}

export interface ShiftDetail {
  id: number
  shift_type_id: number
  shift_type: string
  weight: number
  starts_at: string
  ends_at: string
  slots: number
}

export interface BlockedMember {
  member_id: number
  member_name: string
  reason: 'already_on_shift' | 'busy_at_that_time'
}

export interface UnfilledShift {
  shift_id: number
  missing: number
  /** Who said yes but couldn't be given the shift. Empty: nobody said yes. */
  blocked: BlockedMember[]
}

export interface Proposal {
  assignments: { shift_id: number; member_id: number; member_name: string }[]
  unfilled: UnfilledShift[]
}

export type AssignmentStatus = 'assigned' | 'done' | 'no_show'

export interface AssignmentDetail {
  id: number
  shift_id: number
  member_id: number
  status: AssignmentStatus
  member_name: string
  shift_type: string
  starts_at: string
  ends_at: string
  weight: number
}
export interface Candidate {
  member_id: number
  name: string
  points: number
  said_yes: boolean
  busy: boolean
}

export interface LedgerEntry {
  member_id: number
  change: number
  reason: string
  created_at: string
}

export interface Ledger {
  balances: { member_id: number; name: string; balance: number }[]
  entries: LedgerEntry[]
}

const club = (clubId: number) => `/clubs/${clubId}`
const asCoordinator = (token: string) => ({ 'X-Coordinator-Token': token })

export const coordinatorApi = {
  checkLink: (clubId: number, token: string) =>
    request<ClubPublic>(`${club(clubId)}/coordinator`, { headers: asCoordinator(token) }),
  shifts: (clubId: number) => request<ShiftDetail[]>(`${club(clubId)}/shifts`),
  assignments: (clubId: number, token: string) =>
    request<AssignmentDetail[]>(`${club(clubId)}/assignments`, { headers: asCoordinator(token) }),
  ledger: (clubId: number, token: string) =>
    request<Ledger>(`${club(clubId)}/ledger`, { headers: asCoordinator(token) }),
  generate: (clubId: number, token: string) =>
    request<Proposal>(`${club(clubId)}/schedule/generate`, {
      method: 'POST',
      headers: asCoordinator(token),
    }),
  publish: (clubId: number, token: string) =>
    request<Proposal>(`${club(clubId)}/schedule/publish`, {
      method: 'POST',
      headers: asCoordinator(token),
    }),
  recordOutcome: (assignmentId: number, status: 'done' | 'no_show', token: string) =>
    request<{ id: number; status: AssignmentStatus }>(`/assignments/${assignmentId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
      headers: asCoordinator(token),
    }),
  createClub: (name: string) =>
    request<ClubWithToken>('/clubs', { method: 'POST', body: JSON.stringify({ name }) }),
  memberLinks: (clubId: number, token: string) =>
    request<MemberLink[]>(`${club(clubId)}/members/links`, { headers: asCoordinator(token) }),
  addMember: (clubId: number, token: string, name: string) =>
    request<MemberLink>(`${club(clubId)}/members`, {
      method: 'POST',
      body: JSON.stringify({ name }),
      headers: asCoordinator(token),
    }),
  candidates: (token: string, assignmentId: number) =>
    request<Candidate[]>(`/assignments/${assignmentId}/candidates`, {
      headers: { 'X-Coordinator-Token': token },
    }),
  unassign: (token: string, assignmentId: number) =>
    request<void>(`/assignments/${assignmentId}`, {
      method: 'DELETE',
      headers: { 'X-Coordinator-Token': token },
    }),
  reassign: (token: string, assignmentId: number, memberId: number) =>
    request<AssignmentDetail>(`/assignments/${assignmentId}/member`, {
      method: 'PUT',
      headers: { 'X-Coordinator-Token': token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ member_id: memberId }),
    }),
  shiftCandidates: (clubId: number, token: string, shiftId: number) =>
    request<Candidate[]>(`${club(clubId)}/shifts/${shiftId}/candidates`, {
      headers: asCoordinator(token),
    }),
  assignToShift: (clubId: number, token: string, shiftId: number, memberId: number) =>
    request<{ id: number; shift_id: number; member_id: number; status: AssignmentStatus }>(
      `${club(clubId)}/shifts/${shiftId}/assignments`,
      {
        method: 'POST',
        body: JSON.stringify({ member_id: memberId }),
        headers: asCoordinator(token),
      },
    ),
  shiftTypes: (clubId: number) => request<ShiftTypeInfo[]>(`${club(clubId)}/shift-types`),
  addShiftType: (clubId: number, token: string, name: string, weight: number) =>
    request<ShiftTypeInfo>(`${club(clubId)}/shift-types`, {
      method: 'POST',
      body: JSON.stringify({ name, weight }),
      headers: asCoordinator(token),
    }),
  addWeeklyShifts: (clubId: number, token: string, input: WeeklyShiftsInput) =>
    request<unknown[]>(`${club(clubId)}/shifts/weekly`, {
      method: 'POST',
      body: JSON.stringify(input),
      headers: asCoordinator(token),
    }),
  remove: (clubId: number, token: string, item: SetupItem, id: number) =>
    request<void>(`${club(clubId)}/${item}/${id}`, {
      method: 'DELETE',
      headers: asCoordinator(token),
    }),
}

export interface DemoMemberLink {
  name: string
  points: number
  token: string
}

export interface DemoClub {
  club_id: number
  club_name: string
  coordinator_token: string
  members: DemoMemberLink[]
}

export const demoApi = {
  start: () => request<DemoClub>('/demo', { method: 'POST' }),
}

export interface ClubWithToken extends ClubPublic {
  coordinator_token: string
}

export interface MemberLink {
  id: number
  name: string
  access_token: string
}

export interface ShiftTypeInfo {
  id: number
  name: string
  weight: number
}

export interface WeeklyShiftsInput {
  shift_type_id: number
  starts_at: string
  ends_at: string
  slots: number
  weeks: number
}

export type SetupItem = 'members' | 'shifts' | 'shift-types'
