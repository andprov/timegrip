// Jan 5, 2026 is a Monday - a stable reference to read off Mon..Sun labels.
const MONDAY_REFERENCE = Date.UTC(2026, 0, 5)

export function weekdayLabels(locale: string): string[] {
  const formatter = new Intl.DateTimeFormat(locale, { weekday: 'short' })
  return Array.from({ length: 7 }, (_, i) =>
    formatter.format(new Date(MONDAY_REFERENCE + i * 86400000)),
  )
}

export function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1)
}

export function daysInMonth(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
}

export function endOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0)
}

// Monday = 0 ... Sunday = 6
export function mondayIndex(date: Date): number {
  return (date.getDay() + 6) % 7
}

export function mondayOf(date: Date): Date {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  d.setDate(d.getDate() - mondayIndex(d))
  return d
}

export function isFutureDay(a: Date, today: Date): boolean {
  const normalizedA = new Date(a.getFullYear(), a.getMonth(), a.getDate())
  const normalizedToday = new Date(
    today.getFullYear(),
    today.getMonth(),
    today.getDate(),
  )
  return normalizedA.getTime() > normalizedToday.getTime()
}

export function isBeforeDay(a: Date, b: Date): boolean {
  return isFutureDay(b, a)
}

export function formatMonthLabel(date: Date, locale: string): string {
  return date.toLocaleDateString(locale, {
    month: 'long',
    year: 'numeric',
  })
}

export function toIsoStartOfDay(date: Date): string {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  return d.toISOString()
}

export function toIsoEndOfDay(date: Date): string {
  const d = new Date(date)
  d.setHours(23, 59, 59, 999)
  return d.toISOString()
}
