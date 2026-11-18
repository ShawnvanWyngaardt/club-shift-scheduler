import { readonly, ref } from 'vue'

/*
 * The notice bar under the coordinator tabs: "2 checks saved for Bar, early Saturday."
 * One notice at a time, shared by every coordinator page, so state lives here at
 * module level rather than in a component. It stays a minute, long enough to read
 * after looking away, or until closed.
 */
export interface Notice {
  title: string
  detail?: string
}

export const NOTICE_MS = 60_000

const current = ref<Notice | null>(null)
let timer: ReturnType<typeof setTimeout> | undefined

export function closeNotice() {
  clearTimeout(timer)
  current.value = null
}

export function showNotice(title: string, detail?: string) {
  clearTimeout(timer) // a new notice gets its own full minute
  current.value = { title, detail }
  timer = setTimeout(closeNotice, NOTICE_MS)
}

export function useNotice() {
  return { notice: readonly(current), showNotice, closeNotice }
}
