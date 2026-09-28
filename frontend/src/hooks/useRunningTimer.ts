import { useQuery } from '@tanstack/react-query'

import { getRunningTimer } from '@/api/timers'
import { RUNNING_TIMER_KEY } from '@/lib/timerQueries'

export function useRunningTimer(enabled = true) {
  return useQuery({
    queryKey: RUNNING_TIMER_KEY,
    queryFn: getRunningTimer,
    refetchInterval: 60_000,
    refetchIntervalInBackground: false,
    enabled,
  })
}
