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
