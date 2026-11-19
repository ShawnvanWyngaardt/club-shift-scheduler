import { describe, expect, it } from 'vitest'
import { saveForYourself } from '@/links'

describe('saveForYourself', () => {
  const link = 'https://example.org/c/7/abc+123'
  const { whatsapp, email } = saveForYourself('VV Oranje & Zwart', link)

  it('puts the whole link in a WhatsApp message', () => {
    const text = decodeURIComponent(whatsapp.split('?text=')[1]!)
    expect(text).toBe(`My coordinator link for VV Oranje & Zwart. Keep it private: ${link}`)
  })

  it('writes an email with the club in the subject, and keeps "&" and "+" intact', () => {
    const params = new URLSearchParams(email.replace('mailto:?', ''))
    expect(params.get('subject')).toBe('Coordinator link for VV Oranje & Zwart')
    expect(params.get('body')).toContain(link)
  })
})
