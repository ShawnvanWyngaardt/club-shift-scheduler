import type { DemoClub } from '@/api'

const key = (clubId: number) => `demo-club:${clubId}`

/** Keep the demo's member links in this browser: the API never lists tokens again. */
export function rememberDemo(demo: DemoClub) {
  try {
    localStorage.setItem(key(demo.club_id), JSON.stringify(demo))
  } catch {
    // Storage blocked (some private windows): the demo still works, just without the links panel.
  }
}

export function recallDemo(clubId: number): DemoClub | null {
  try {
    const saved = localStorage.getItem(key(clubId))
    return saved ? (JSON.parse(saved) as DemoClub) : null
  } catch {
    return null
  }
}

//export const memberUrl = (token: string) => `${window.location.origin}/m/${token}`
