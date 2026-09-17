import { useAuth } from '@/auth/useAuth'
import { resolveHour12 } from '@/lib/timeFormat'

export function useTimeFormat() {
  const { user } = useAuth()
  const preference = user?.time_format ?? '24h'
  return { preference, hour12: resolveHour12(preference) }
}
