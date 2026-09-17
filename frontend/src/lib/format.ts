const ISO_DURATION_RE =
  /^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$/

export function parseIsoDurationSeconds(iso: string): number {
  const match = ISO_DURATION_RE.exec(iso)
  if (!match) return 0
  const [, days, hours, minutes, seconds] = match
  return (
    Number(days ?? 0) * 86400 +
    Number(hours ?? 0) * 3600 +
    Number(minutes ?? 0) * 60 +
    Number(seconds ?? 0)
  )
}

export function formatSecondsAsClock(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${pad(hours)}:${pad(minutes)}`
}

export function formatCountdown(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

export function formatDurationClock(iso: string | null): string {
  if (!iso) return '–'
  return formatSecondsAsClock(Math.floor(parseIsoDurationSeconds(iso)))
}

export function formatDurationBetween(
  startIso: string,
  endIso: string,
  units: { hour: string; minute: string } = { hour: 'h', minute: 'm' },
): string {
  const totalMinutes = Math.max(
    0,
    Math.round(
      (new Date(endIso).getTime() - new Date(startIso).getTime()) / 60000,
    ),
  )
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  if (hours === 0 && minutes === 0) return `0${units.minute}`
  if (hours === 0) return `${minutes}${units.minute}`
  if (minutes === 0) return `${hours}${units.hour}`
  return `${hours}${units.hour} ${minutes}${units.minute}`
}

export function formatElapsed(startIso: string, now: Date): string {
  const totalSeconds = Math.max(
    0,
    Math.floor((now.getTime() - new Date(startIso).getTime()) / 1000),
  )
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`
}

export function formatAmountPlain(value: string | number | null): string {
  if (value === null) return '–'
  return Number(value).toFixed(2)
}

export function formatAmount(value: string | number | null): string {
  if (value === null) return '–'
  const num = Number(value)
  const [intPart, fracPart] = Math.abs(num).toFixed(2).split('.')
  const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
  const sign = num < 0 ? '-' : ''
  return `${sign}${grouped}.${fracPart}`
}

export function formatDate(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${pad(date.getDate())}.${pad(date.getMonth() + 1)}.${date.getFullYear()}`
}

export function formatTime(date: Date, hour12: boolean): string {
  return date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    hour12,
  })
}

export function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}
