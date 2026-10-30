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
