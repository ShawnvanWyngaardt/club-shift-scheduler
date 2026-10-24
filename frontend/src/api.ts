export interface MemberProfile {
  name: string
  club_id: number
  club_name: string
  balance: number
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
    const detail = typeof body.detail === 'string' ? body.detail : response.statusText
    throw new ApiError(response.status, detail)
  }
  return response.json() as Promise<T>
}

const member = (token: string) => `/me/${encodeURIComponent(token)}`

export const api = {
  me: (token: string) => request<MemberProfile>(member(token)),
  myShifts: (token: string) => request<MyShift[]>(`${member(token)}/shifts`),
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

export interface Proposal {
  assignments: { shift_id: number; member_id: number; member_name: string }[]
  unfilled: { shift_id: number; missing: number }[]
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

export interface Ledger {
  balances: { member_id: number; name: string; balance: number }[]
}

const club = (clubId: number) => `/clubs/${clubId}`
const asCoordinator = (token: string) => ({ 'X-Coordinator-Token': token })

export const coordinatorApi = {
  checkLink: (clubId: number, token: string) =>
    request<ClubPublic>(`${club(clubId)}/coordinator`, { headers: asCoordinator(token) }),
  shifts: (clubId: number) => request<ShiftDetail[]>(`${club(clubId)}/shifts`),
  assignments: (clubId: number) => request<AssignmentDetail[]>(`${club(clubId)}/assignments`),
  ledger: (clubId: number) => request<Ledger>(`${club(clubId)}/ledger`),
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
}
