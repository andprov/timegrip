import type { TimeFormatPreference } from '@/api/types'

export const TIME_FORMAT_LABELS: Record<TimeFormatPreference, string> = {
  '12h': '12-hour',
  '24h': '24-hour',
}

export function resolveHour12(preference: TimeFormatPreference): boolean {
  return preference === '12h'
}
