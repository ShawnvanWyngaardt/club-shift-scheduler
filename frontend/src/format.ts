/**
 * Counts with the right word: "1 point", "3 points", "+1 point", "−2 points".
 * Intl.PluralRules knows each language's rules, so Dutch later is a matter of
 * passing 'nl' and the Dutch words, with no if-statements per language.
 */
const rules = new Intl.PluralRules('en')

/** "1 slot", "2 slots". Pass the plural when it isn't the singular plus "s". */
export function count(n: number, one: string, other = `${one}s`): string {
  return `${n} ${rules.select(Math.abs(n)) === 'one' ? one : other}`
}

/** Only the word, for when the number is styled separately: "shift" or "shifts". */
export function word(n: number, one: string, other = `${one}s`): string {
  return rules.select(Math.abs(n)) === 'one' ? one : other
}

/** A signed number: "+3", "−2" (a real minus sign) or "0". */
export function signed(n: number): string {
  if (n > 0) return `+${n}`
  if (n < 0) return `−${Math.abs(n)}`
  return '0'
}

/** Points, optionally signed or short: "1 point", "+3 points", "1 pt", "−2 pts". */
export function points(n: number, { sign = false, short = false } = {}): string {
  const [one, other] = short ? ['pt', 'pts'] : ['point', 'points']
  const value = sign ? signed(n) : String(n)
  return `${value} ${rules.select(Math.abs(n)) === 'one' ? one : other}`
}
