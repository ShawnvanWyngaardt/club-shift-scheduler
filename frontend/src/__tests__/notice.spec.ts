import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { NOTICE_MS, useNotice } from '../composables/useNotice'

describe('useNotice', () => {
  const { notice, showNotice, closeNotice } = useNotice()

  beforeEach(() => vi.useFakeTimers())
  afterEach(() => {
    closeNotice()
    vi.useRealTimers()
  })

  it('shows a notice and hides it after a minute', () => {
    showNotice('Week 48 published.', 'Members now see their shifts.')
    expect(notice.value).toEqual({
      title: 'Week 48 published.',
      detail: 'Members now see their shifts.',
    })
    vi.advanceTimersByTime(NOTICE_MS - 1)
    expect(notice.value).not.toBeNull()
    vi.advanceTimersByTime(1)
    expect(notice.value).toBeNull()
  })

  it('gives a new notice its own full minute', () => {
    showNotice('First')
    vi.advanceTimersByTime(NOTICE_MS - 1000)
    showNotice('Second')
    vi.advanceTimersByTime(NOTICE_MS - 1)
    expect(notice.value?.title).toBe('Second')
  })

  it('closes straight away with the close button', () => {
    showNotice('Saved')
    closeNotice()
    expect(notice.value).toBeNull()
  })
})
