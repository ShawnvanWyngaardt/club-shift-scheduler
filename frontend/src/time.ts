const CLUB_TIMEZONE = 'Europe/Amsterdam'

const dayFormat = new Intl.DateTimeFormat('en-GB', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  timeZone: CLUB_TIMEZONE,
})

const timeFormat = new Intl.DateTimeFormat('en-GB', {
  hour: '2-digit',
  minute: '2-digit',
  timeZone: CLUB_TIMEZONE,
})

export const formatDay = (iso: string) => dayFormat.format(new Date(iso))

export const formatTimeRange = (start: string, end: string) =>
  `${timeFormat.format(new Date(start))} – ${timeFormat.format(new Date(end))}`

/** Group anything with a start time by its Amsterdam day, keeping the order it came in. */
export function groupByDay<T extends { starts_at: string }>(items: T[]) {
  const groups = new Map<string, T[]>()
  for (const item of items) {
    const day = formatDay(item.starts_at)
    groups.set(day, [...(groups.get(day) ?? []), item])
  }
  return [...groups].map(([day, list]) => ({ day, items: list }))
}

/** The UTC moment for a date and time on the club's clock, as the API expects it. */
export function amsterdamToIso(date: string, time: string): string {
  const wallClockAsUtc = new Date(`${date}T${time}:00Z`)
  const offset = amsterdamOffsetMinutes(wallClockAsUtc)
  return new Date(wallClockAsUtc.getTime() - offset * 60_000).toISOString()
}

function amsterdamOffsetMinutes(at: Date): number {
  const zoneName =
    new Intl.DateTimeFormat('en-GB', { timeZone: CLUB_TIMEZONE, timeZoneName: 'longOffset' })
      .formatToParts(at)
      .find((part) => part.type === 'timeZoneName')?.value ?? 'GMT'
  const match = /GMT([+-])(\d{2}):(\d{2})/.exec(zoneName)
  if (!match) return 0 // a plain "GMT" means no offset
  const minutes = Number(match[2]) * 60 + Number(match[3])
  return match[1] === '-' ? -minutes : minutes
}
