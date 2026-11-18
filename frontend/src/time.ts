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

const shortDayFormat = new Intl.DateTimeFormat('en-GB', {
  weekday: 'short',
  day: 'numeric',
  timeZone: CLUB_TIMEZONE,
})

/** "Sat 28", for narrow places like the availability grid's column headers. */
export const formatShortDay = (iso: string) => shortDayFormat.format(new Date(iso))

/** "07:00", the start time on the club's clock. */
export const formatTime = (iso: string) => timeFormat.format(new Date(iso))

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

const DAY = 86_400_000

// "2026-11-16": en-CA writes dates as year-month-day, which is easy to split.
const isoDateFormat = new Intl.DateTimeFormat('en-CA', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  timeZone: CLUB_TIMEZONE,
})
const shortDateFormat = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
  timeZone: 'UTC',
})

/** The club's calendar date for a moment, as midnight UTC, so date sums ignore clock changes. */
function clubDate(iso: string): Date {
  const [year = 1970, month = 1, day = 1] = isoDateFormat.format(new Date(iso)).split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day))
}

export interface ClubWeek {
  /** "2026-W49": sorts in order and is safe in a URL. */
  key: string
  number: number
  /** "16 – 22 Nov" or "30 Nov – 6 Dec" */
  dates: string
  /** Monday 00:00 club time, as the API expects it. */
  start: string
  /** The next Monday 00:00: the end is exclusive, like the API's `to`. */
  end: string
}

function weekStartingOn(monday: Date): ClubWeek {
  // ISO weeks belong to the year their Thursday is in; week 1 holds 4 January.
  const year = new Date(monday.getTime() + 3 * DAY).getUTCFullYear()
  const number = 1 + Math.round((monday.getTime() - firstMondayOf(year)) / (7 * DAY))
  const sunday = new Date(monday.getTime() + 6 * DAY)
  const nextMonday = new Date(monday.getTime() + 7 * DAY)

  const sameMonth = monday.getUTCMonth() === sunday.getUTCMonth()
  const from = sameMonth ? String(monday.getUTCDate()) : shortDateFormat.format(monday)
  const ymd = (date: Date) => date.toISOString().slice(0, 10)
  return {
    key: `${year}-W${String(number).padStart(2, '0')}`,
    number,
    dates: `${from} – ${shortDateFormat.format(sunday)}`,
    start: amsterdamToIso(ymd(monday), '00:00'),
    end: amsterdamToIso(ymd(nextMonday), '00:00'),
  }
}

function firstMondayOf(year: number): number {
  const jan4 = new Date(Date.UTC(year, 0, 4))
  return jan4.getTime() - ((jan4.getUTCDay() + 6) % 7) * DAY
}

/** The ISO week (Monday to Sunday, on the club's clock) a moment falls in. */
export function weekOf(iso: string): ClubWeek {
  const date = clubDate(iso)
  return weekStartingOn(new Date(date.getTime() - ((date.getUTCDay() + 6) % 7) * DAY))
}

/** A week from its key in the URL, or null for a key that isn't a real week. */
export function weekFromKey(key: string): ClubWeek | null {
  const match = /^(\d{4})-W(\d{2})$/.exec(key)
  if (!match) return null
  const monday = new Date(firstMondayOf(Number(match[1])) + (Number(match[2]) - 1) * 7 * DAY)
  const week = weekStartingOn(monday)
  return week.key === key ? week : null // "2027-W53" doesn't exist: it would roll into 2028
}

/** This week and the ones after it: what the Overview shows. */
export function weeksFrom(iso: string, count: number): ClubWeek[] {
  const first = weekOf(iso)
  const monday = clubDate(first.start)
  return Array.from({ length: count }, (_, i) =>
    weekStartingOn(new Date(monday.getTime() + i * 7 * DAY)),
  )
}

/** Group anything with a start time by its week, in the order the weeks first appear. */
export function groupByWeek<T extends { starts_at: string }>(items: T[]) {
  const groups = new Map<string, { week: ClubWeek; items: T[] }>()
  for (const item of items) {
    const week = weekOf(item.starts_at)
    const group = groups.get(week.key) ?? { week, items: [] }
    group.items.push(item)
    groups.set(week.key, group)
  }
  return [...groups.values()]
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
