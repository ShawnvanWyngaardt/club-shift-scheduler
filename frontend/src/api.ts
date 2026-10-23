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
