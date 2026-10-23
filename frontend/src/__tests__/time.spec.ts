import { describe, expect, it } from 'vitest'
import { formatDay, formatTimeRange } from '@/time'

describe('time formatting', () => {
  it('shows UTC times from the API in Amsterdam time', () => {
    expect(formatTimeRange('2026-10-24T05:00:00Z', '2026-10-24T09:00:00Z')).toBe('07:00 – 11:00')
  })

  it('uses Amsterdam winter time after the clocks change', () => {
    expect(formatTimeRange('2026-10-31T06:00:00Z', '2026-10-31T10:00:00Z')).toBe('07:00 – 11:00')
  })

  it('puts a late-evening UTC time on the right Amsterdam day', () => {
    expect(formatDay('2026-10-23T23:30:00Z')).toBe('Saturday 24 October')
  })
})
