export const memberUrl = (token: string) => `${window.location.origin}/m/${token}`

export const coordinatorUrl = (clubId: number, token: string) =>
  `${window.location.origin}/c/${clubId}/${token}`

export const whatsappUrl = (text: string) => `https://wa.me/?text=${encodeURIComponent(text)}`

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

/**
 * Ways for a new coordinator to keep their link: a WhatsApp chat with themselves,
 * or an email to themselves. It's the only way back in, so more than one place helps.
 */
export function saveForYourself(clubName: string, link: string) {
  const text = `My coordinator link for ${clubName}. Keep it private: ${link}`
  const subject = `Coordinator link for ${clubName}`
  return {
    whatsapp: whatsappUrl(text),
    email: `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(text)}`,
  }
}
