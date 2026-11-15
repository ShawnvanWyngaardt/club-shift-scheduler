import { describe, expect, it } from 'vitest'
import { count, points, signed } from '../format'

describe('count', () => {
  it('uses the singular for one, and the plural otherwise', () => {
    expect(count(1, 'slot')).toBe('1 slot')
    expect(count(0, 'slot')).toBe('0 slots')
    expect(count(2, 'slot')).toBe('2 slots')
  })

  it('takes an irregular plural', () => {
    expect(count(1, 'person', 'people')).toBe('1 person')
    expect(count(3, 'person', 'people')).toBe('3 people')
  })
})

describe('signed', () => {
  it('shows a plus, a real minus sign, or zero', () => {
    expect(signed(3)).toBe('+3')
    expect(signed(-2)).toBe('−2')
    expect(signed(0)).toBe('0')
  })
})

describe('points', () => {
  it('handles one, many and zero', () => {
    expect(points(1)).toBe('1 point')
    expect(points(3)).toBe('3 points')
    expect(points(0)).toBe('0 points')
  })

  it('signs and shortens', () => {
    expect(points(1, { sign: true })).toBe('+1 point')
    expect(points(-1, { sign: true })).toBe('−1 point')
    expect(points(-2, { sign: true })).toBe('−2 points')
    expect(points(1, { short: true })).toBe('1 pt')
    expect(points(4, { short: true })).toBe('4 pts')
  })
})
