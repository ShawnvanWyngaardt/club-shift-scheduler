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
